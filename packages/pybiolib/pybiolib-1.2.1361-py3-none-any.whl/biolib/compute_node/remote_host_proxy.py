import base64
import io
import ipaddress
import tarfile
import time
from urllib.parse import urlparse

from docker.models.containers import Container
from docker.models.networks import Network
from docker.types import EndpointConfig

from biolib import utils
from biolib.biolib_api_client import BiolibApiClient, RemoteHost
from biolib.biolib_docker_client import BiolibDockerClient
from biolib.biolib_errors import BioLibError
from biolib.biolib_logging import logger_no_user_data
from biolib.compute_node.cloud_utils import CloudUtils
from biolib.compute_node.utils import BIOLIB_PROXY_NETWORK_NAME
from biolib.compute_node.webserver.proxy_utils import get_biolib_nginx_proxy_image
from biolib.typing_utils import Dict, List, Optional


def get_static_ip_from_network(network: Network, offset: int = 2) -> str:
    ipam_config = network.attrs['IPAM']['Config']
    if not ipam_config:
        raise BioLibError(f'Network {network.name} has no IPAM configuration')

    subnet_str = ipam_config[0]['Subnet']
    subnet = ipaddress.ip_network(subnet_str, strict=False)

    static_ip = str(subnet.network_address + offset)

    return static_ip


# Prepare for remote hosts with specified port
class RemoteHostExtended(RemoteHost):
    ports: List[int]


class RemoteHostMapping:
    def __init__(self, hostname: str, ports: List[int], network: Network, static_ip: str):
        self.hostname = hostname
        self.ports = ports
        self.network = network
        self.static_ip = static_ip


class RemoteHostProxy:
    def __init__(
        self,
        remote_host_mappings: List[RemoteHostMapping],
        job_id: str,
        app_caller_network: Optional[Network] = None,
    ):
        self._remote_host_mappings = remote_host_mappings
        self._app_caller_network = app_caller_network
        self.is_app_caller_proxy = app_caller_network is not None

        if not job_id:
            raise Exception('RemoteHostProxy missing argument "job_id"')

        suffix = '-AppCallerProxy' if app_caller_network else ''
        self._name = f'biolib-remote-host-proxy-{job_id}{suffix}'
        self._job_uuid = job_id
        self._container: Optional[Container] = None
        self._docker = BiolibDockerClient().get_docker_client()

    def get_hostname_to_ip_mapping(self) -> Dict[str, str]:
        return {mapping.hostname: mapping.static_ip for mapping in self._remote_host_mappings}

    def get_remote_host_networks(self) -> List[Network]:
        networks = [mapping.network for mapping in self._remote_host_mappings]
        return networks

    def get_ip_address_on_network(self, network: Network) -> str:
        if not self._container:
            raise BioLibError('RemoteHostProxy not yet started')

        container_networks = self._container.attrs['NetworkSettings']['Networks']
        if network.name in container_networks:
            ip_address: str = container_networks[network.name]['IPAddress']
            if not ip_address:
                raise BioLibError(f'No IP address found for network {network.name}')
            return ip_address

        raise BioLibError(f'RemoteHostProxy not connected to network {network.name}')

    def start(self) -> None:
        docker = BiolibDockerClient.get_docker_client()

        networking_config: Optional[Dict[str, EndpointConfig]] = (
            None
            if not self.is_app_caller_proxy
            else {
                BIOLIB_PROXY_NETWORK_NAME: docker.api.create_endpoint_config(
                    aliases=[f'biolib-app-caller-proxy-{self._job_uuid}']
                )
            }
        )

        for index in range(3):
            logger_no_user_data.debug(f'Attempt {index} at creating RemoteHostProxy container "{self._name}"...')
            try:
                self._container = docker.containers.create(
                    detach=True,
                    image=get_biolib_nginx_proxy_image(),
                    name=self._name,
                    network=BIOLIB_PROXY_NETWORK_NAME,
                    networking_config=networking_config,
                )
                break
            except Exception as error:
                logger_no_user_data.exception(f'Failed to create container "{self._name}" hit error: {error}')

            logger_no_user_data.debug('Sleeping before re-trying container creation...')
            time.sleep(3)

        if not self._container or not self._container.id:
            raise BioLibError(f'Exceeded re-try limit for creating container {self._name}')

        for mapping in self._remote_host_mappings:
            mapping.network.connect(self._container.id, ipv4_address=mapping.static_ip)
            logger_no_user_data.debug(
                f'Connected proxy to network {mapping.network.name} with static IP {mapping.static_ip}'
            )

        if self._app_caller_network:
            self._app_caller_network.connect(self._container.id)
            logger_no_user_data.debug(
                f'Connected app caller proxy to network {self._app_caller_network.name}'
            )

        self._write_nginx_config_to_container()

        self._container.start()

        proxy_is_ready = False
        for retry_count in range(1, 5):
            time.sleep(0.5 * retry_count)
            # Use the container logs as a health check.
            # By using logs instead of a http endpoint on the NGINX we avoid publishing a port of container to the host
            container_logs = self._container.logs()
            if b'ready for start up\n' in container_logs or b'start worker process ' in container_logs:
                proxy_is_ready = True
                break

        if not proxy_is_ready:
            self.terminate()
            raise Exception('RemoteHostProxy did not start properly')

        self._container.reload()

    def terminate(self):
        # TODO: Implement nice error handling in this method

        if self._container:
            self._container.remove(force=True)

    def _write_nginx_config_to_container(self) -> None:
        if not self._container:
            raise Exception('RemoteHostProxy container not defined when attempting to write NGINX config')

        docker = BiolibDockerClient.get_docker_client()
        upstream_hostname = urlparse(BiolibApiClient.get().base_url).hostname
        if self.is_app_caller_proxy:
            if not utils.IS_RUNNING_IN_CLOUD:
                raise BioLibError('Calling apps inside apps is not supported in local compute environment')

            logger_no_user_data.debug(f'Job "{self._job_uuid}" writing config for and starting App Caller Proxy...')
            config = CloudUtils.get_webserver_config()
            compute_node_uuid = config['compute_node_info']['public_id']
            compute_node_auth_token = config['compute_node_info']['auth_token']

            # TODO: Get access_token from new API class instead
            access_token = BiolibApiClient.get().access_token
            bearer_token = f'Bearer {access_token}' if access_token else ''

            biolib_index_basic_auth = f'compute_node|admin:{compute_node_auth_token},{self._job_uuid}'
            biolib_index_basic_auth_base64 = base64.b64encode(biolib_index_basic_auth.encode('utf-8')).decode('utf-8')

            nginx_config = f"""
events {{
  worker_connections  1024;
}}

http {{
    client_max_body_size 0;
    map $request_method $bearer_token_on_post {{
        POST       "{bearer_token}";
        default    "";
    }}

    map $request_method $bearer_token_on_get {{
        GET        "{bearer_token}";
        default    "";
    }}

    map $request_method $bearer_token_on_patch_and_get {{
        PATCH      "{bearer_token}";
        GET        "{bearer_token}";
        default    "";
    }}

    server {{
        listen       80;
        resolver 127.0.0.11 ipv6=off valid=30s;
        set $upstream_hostname {upstream_hostname};

        location ~* "^/api/jobs/cloud/(?<job_id>[a-z0-9-]{{36}})/status/$" {{
            proxy_pass               https://$upstream_hostname/api/jobs/cloud/$job_id/status/;
            proxy_set_header         authorization $bearer_token_on_get;
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/cloud/$" {{
            # Note: Using $1 here as URI part from regex must be used for proxy_pass
            proxy_pass               https://$upstream_hostname/api/jobs/cloud/$1;
            proxy_set_header         authorization $bearer_token_on_post;
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/(?<job_id>[a-z0-9-]{{36}})/storage/input/start_upload/$" {{
            proxy_pass               https://$upstream_hostname/api/jobs/$job_id/storage/input/start_upload/;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/(?<job_id>[a-z0-9-]{{36}})/storage/input/presigned_upload_url/$" {{
            proxy_pass               https://$upstream_hostname/api/jobs/$job_id/storage/input/presigned_upload_url/$is_args$args;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/(?<job_id>[a-z0-9-]{{36}})/storage/input/complete_upload/$" {{
            proxy_pass               https://$upstream_hostname/api/jobs/$job_id/storage/input/complete_upload/;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/(?<job_id>[a-z0-9-]{{36}})/main_result/$" {{
            proxy_pass                  https://$upstream_hostname/api/jobs/$job_id/main_result/;
            proxy_set_header            authorization "";
            proxy_set_header            cookie "";
            proxy_pass_request_headers  on;
            proxy_ssl_server_name       on;
        }}

        location ~* "^/api/jobs/(?<job_id>[a-z0-9-]{{36}})/$" {{
            proxy_pass               https://$upstream_hostname/api/jobs/$job_id/;
            proxy_set_header         authorization $bearer_token_on_patch_and_get;
            proxy_set_header         caller-job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/create_job_with_data/$" {{
            # Note: Using $1 here as URI part from regex must be used for proxy_pass
            proxy_pass               https://$upstream_hostname/api/jobs/create_job_with_data/$1;
            proxy_set_header         authorization $bearer_token_on_post;
            proxy_set_header         caller-job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~* "^/api/jobs/$" {{
            # Note: Using $1 here as URI part from regex must be used for proxy_pass
            proxy_pass               https://$upstream_hostname/api/jobs/$1;
            proxy_set_header         authorization $bearer_token_on_post;
            proxy_set_header         caller-job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~ "^/api/jobs/{self._job_uuid}/notes/$" {{
            # Note: Using $1 here as URI part from regex must be used for proxy_pass
            proxy_pass               https://$upstream_hostname/api/jobs/{self._job_uuid}/notes/$1;
            proxy_set_header         authorization "";
            proxy_set_header         job-auth-token "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         compute-node-uuid "{compute_node_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location ~ "^/api/auth/oauth-token-exchange/$" {{
            # Note: Using $1 here as URI part from regex must be used for proxy_pass
            proxy_pass               https://$upstream_hostname/api/auth/oauth-token-exchange/$1;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/lfs/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/app/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/resources/data-records/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/resources/versions/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/proxy/files/data-record-versions/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         compute-node-auth-token "{compute_node_auth_token}";
            proxy_set_header         job-uuid "{self._job_uuid}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /api/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /proxy/storage/job-storage/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /proxy/storage/lfs/versions/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /proxy/cloud/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location /proxy/index/ {{
            proxy_pass               https://$upstream_hostname$request_uri;
            proxy_set_header         authorization "Basic {biolib_index_basic_auth_base64}";
            proxy_set_header         cookie "";
            proxy_ssl_server_name    on;
        }}

        location / {{
            return 404 "Not found";
        }}
    }}

    server {{
        listen       1080;
        resolver 127.0.0.11 ipv6=off valid=30s;

        if ($http_biolib_result_uuid != "{self._job_uuid}") {{
            return 403 "Invalid or missing biolib-result-uuid header";
        }}

        if ($http_biolib_result_port = "") {{
            return 400 "Missing biolib-result-port header";
        }}

        location / {{
            proxy_pass               http://main:$http_biolib_result_port$request_uri;
            proxy_set_header         biolib-result-uuid "";
            proxy_set_header         biolib-result-port "";
            proxy_pass_request_headers on;
        }}
    }}
}}
"""
        else:
            port_to_mappings: Dict[int, List[RemoteHostMapping]] = {}
            for mapping in self._remote_host_mappings:
                for port in mapping.ports:
                    if port not in port_to_mappings:
                        port_to_mappings[port] = []
                    port_to_mappings[port].append(mapping)

            nginx_config = """
events {}
error_log /dev/stdout info;
stream {
    resolver 127.0.0.11 valid=30s;"""

            for port, mappings in port_to_mappings.items():
                nginx_config += f"""
    map $server_addr $backend_{port} {{"""
                for mapping in mappings:
                    nginx_config += f'\n        {mapping.static_ip} {mapping.hostname}:{port};'

                nginx_config += f"""
    }}
    server {{
        listen 0.0.0.0:{port};
        proxy_pass $backend_{port};
    }}
    server {{
        listen 0.0.0.0:{port} udp;
        proxy_pass $backend_{port};
    }}"""

            nginx_config += """
}
"""

        nginx_config_bytes = nginx_config.encode()
        tarfile_in_memory = io.BytesIO()
        with tarfile.open(fileobj=tarfile_in_memory, mode='w:gz') as tar:
            info = tarfile.TarInfo('/nginx.conf')
            info.size = len(nginx_config_bytes)
            tar.addfile(info, io.BytesIO(nginx_config_bytes))

        tarfile_bytes = tarfile_in_memory.getvalue()
        tarfile_in_memory.close()
        docker.api.put_archive(self._container.id, '/etc/nginx', tarfile_bytes)
