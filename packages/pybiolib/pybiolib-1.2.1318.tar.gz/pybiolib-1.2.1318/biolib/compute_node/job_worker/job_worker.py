import io
import json
import multiprocessing
import os
import shlex
import signal
import socket
import sys
import tempfile
import zipfile
from queue import Queue
from time import time
from types import FrameType

from docker.models.networks import Network  # type: ignore
from docker.types import IPAMConfig, IPAMPool

from biolib import utils
from biolib._internal.http_client import HttpClient
from biolib.biolib_api_client import (
    AppVersionOnJob,
    BiolibApiClient,
    CreatedJobDict,
    JobWrapper,
    Module,
    ModuleEnvironment,
)
from biolib.biolib_api_client.biolib_job_api import BiolibJobApi
from biolib.biolib_binary_format import (
    InMemoryIndexableBuffer,
    ModuleInput,
    ModuleOutputV2,
    SavedJob,
    SystemException,
    SystemStatusUpdate,
)
from biolib.biolib_binary_format.stdout_and_stderr import StdoutAndStderr
from biolib.biolib_docker_client import BiolibDockerClient
from biolib.biolib_errors import BioLibError, DockerContainerNotFoundDuringExecutionException, StorageDownloadFailed
from biolib.biolib_logging import logger, logger_no_user_data
from biolib.compute_node.job_worker.executors import DockerExecutor
from biolib.compute_node.job_worker.executors.types import LocalExecutorOptions, StatusUpdate
from biolib.compute_node.job_worker.job_legacy_input_wait_timeout_thread import JobLegacyInputWaitTimeout
from biolib.compute_node.job_worker.job_max_runtime_timer_thread import JobMaxRuntimeTimerThread
from biolib.compute_node.job_worker.job_storage import JobStorage
from biolib.compute_node.job_worker.large_file_system import LargeFileSystem
from biolib.compute_node.job_worker.mappings import Mappings, path_without_first_folder
from biolib.compute_node.job_worker.utils import ComputeProcessException, log_disk_and_memory_usage_info
from biolib.compute_node.remote_host_proxy import RemoteHostMapping, RemoteHostProxy, get_static_ip_from_network
from biolib.compute_node.socker_listener_thread import SocketListenerThread
from biolib.compute_node.socket_sender_thread import SocketSenderThread
from biolib.compute_node.utils import SystemExceptionCodeMap, SystemExceptionCodes, get_package_type
from biolib.typing_utils import Dict, List, Optional

SOCKET_HOST = '127.0.0.1'


class JobWorkerProcess(multiprocessing.Process):

    # note: this method is run in the parent process
    def __init__(self, socket_port: int, log_level: int):
        super().__init__()
        self._socket_port = socket_port
        self._log_level = log_level

    # note: this method is run in the newly started process once called with .start()
    def run(self) -> None:
        JobWorker(self._socket_port, self._log_level).run_handle_message_loop()


class JobWorker:
    _STOP_HANDLE_MESSAGE_LOOP = b'STOP_HANDLE_MESSAGE_LOOP'

    def __init__(self, socket_port: Optional[int] = None, log_level: Optional[int] = None):
        try:
            if log_level:
                logger.setLevel(log_level)

            # handle interrupt from keyboard (CTRL + C)
            signal.signal(signal.SIGINT, self._handle_exit_gracefully)
            # handle termination signal from parent
            signal.signal(signal.SIGTERM, self._handle_exit_gracefully)

            self._socket_port = socket_port
            self._received_messages_queue: Queue = Queue()
            self._messages_to_send_queue: Queue = Queue()
            self._legacy_input_wait_timeout_thread: Optional[JobLegacyInputWaitTimeout] = None

            self._app_version_id_to_runtime_zip: Dict[str, bytes] = {}
            self._jobs: Dict[str, CreatedJobDict] = {}
            self._root_job_wrapper: Optional[JobWrapper] = None

            self._remote_host_proxies: List[RemoteHostProxy] = []
            self._internal_network: Optional[Network] = None
            self._executors: List[DockerExecutor] = []
            self.is_cleaning_up: bool = False

            self.job_temporary_dir: Optional[str] = None

        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_INIT_COMPUTE_PROCESS_VARIABLES.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

        if socket_port:
            self._connect_to_parent()

    def _handle_exit_gracefully(
            self,
            signum: int,
            frame: Optional[FrameType],  # pylint: disable=unused-argument
    ) -> None:
        job_id = self._root_job_wrapper["job"]["public_id"] if self._root_job_wrapper else None
        logger_no_user_data.debug(
            f'_JobWorker ({job_id}) got exit signal {signal.Signals(signum).name}'  # pylint: disable=no-member
        )
        self._received_messages_queue.put(self._STOP_HANDLE_MESSAGE_LOOP)
        self._cleanup()

    def run_handle_message_loop(self):
        logger_no_user_data.debug(f'Started JobWorkerProcess {os.getpid()}')
        while True:
            try:
                package = self._received_messages_queue.get()
                if package == self._STOP_HANDLE_MESSAGE_LOOP:
                    break

                package_type = get_package_type(package)
                if package_type == 'SavedJob':
                    self._handle_save_job_wrapper(package)
                    if utils.IS_RUNNING_IN_CLOUD:
                        job = self._root_job_wrapper['job']
                        job_uuid = job['public_id']
                        max_runtime_in_seconds = self._root_job_wrapper['cloud_job']['max_runtime_in_seconds']
                        logger_no_user_data.debug(
                            f'Job "{job_uuid}" will have max run time set to {max_runtime_in_seconds} seconds'
                        )
                        JobMaxRuntimeTimerThread(
                            job_worker=self,
                            max_runtime_in_seconds=max_runtime_in_seconds,
                        ).start()

                        try:
                            module_input_path = os.path.join(self.job_temporary_dir, JobStorage.module_input_file_name)
                            JobStorage.download_module_input(job=job, path=module_input_path)
                        except StorageDownloadFailed:
                            # Expect module input to be handled in a separate ModuleInput package
                            self._legacy_input_wait_timeout_thread = JobLegacyInputWaitTimeout(
                                input_max_wait_in_seconds=120,
                                job_uuid=job_uuid,
                                send_system_exception=self.send_system_exception,
                            )
                            self._legacy_input_wait_timeout_thread.start()
                            continue
                        except Exception as error:
                            raise error

                        try:
                            self._run_root_job(module_input_path)

                        # This error occurs when trying to access the container after the job worker has cleaned it up.
                        # In that case stop the computation.
                        except DockerContainerNotFoundDuringExecutionException as err:
                            if self.is_cleaning_up:
                                break
                            else:
                                raise err

                elif package_type == 'ModuleInput':
                    if not self._root_job_wrapper:
                        raise Exception('No job saved yet')

                    if self._legacy_input_wait_timeout_thread:
                        self._legacy_input_wait_timeout_thread.stop()

                    try:
                        module_input_path = os.path.join(self.job_temporary_dir, JobStorage.module_input_file_name)
                        open(module_input_path, 'wb').write(package)
                        self._run_root_job(module_input_path)

                    # This error occurs when trying to access the container after the job worker has cleaned it up.
                    # In that case stop the computation.
                    except DockerContainerNotFoundDuringExecutionException as err:
                        if self.is_cleaning_up:
                            break
                        else:
                            raise err

                else:
                    logger_no_user_data.error('Package type from parent was not recognized')

                self._received_messages_queue.task_done()
            except ComputeProcessException:
                continue

            except Exception as exception:
                raise ComputeProcessException(
                    exception,
                    SystemExceptionCodes.UNKNOWN_COMPUTE_PROCESS_ERROR.value,
                    self.send_system_exception
                ) from exception

    def _cleanup(self) -> None:
        self.is_cleaning_up = True

        logger_no_user_data.debug('Cleaning up executers...')
        for executor in self._executors:
            executor.cleanup()

        proxy_count = len(self._remote_host_proxies)
        cleaned_networks = set()
        if proxy_count > 0:
            logger_no_user_data.debug('Cleaning up proxies...')
            proxy_cleanup_start_time = time()

            for proxy in self._remote_host_proxies:
                try:
                    proxy.terminate()
                except Exception as exception:  # pylint: disable=broad-except
                    logger_no_user_data.error('Failed to clean up remote host proxy')
                    logger.error(exception)

                for network in proxy.get_remote_host_networks():
                    try:
                        self._cleanup_network(network)
                        cleaned_networks.add(network.id)
                    except Exception as exception:  # pylint: disable=broad-except
                        logger_no_user_data.error(f'Failed to clean up network {network.name}')
                        logger.error(exception)

            self._remote_host_proxies = []
            logger_no_user_data.debug(f'Cleaned up {proxy_count} proxies in {time() - proxy_cleanup_start_time}')

        logger_no_user_data.debug('Cleaning up networks...')
        if self._internal_network and self._internal_network.id not in cleaned_networks:
            self._cleanup_network(self._internal_network)
        self._internal_network = None
        logger_no_user_data.debug('Cleaned up networks...')

    @staticmethod
    def _cleanup_network(network: Optional[Network]) -> None:
        if network:
            network_cleanup_start_time = time()
            network_name = network
            try:
                network.remove()
            except Exception as exception:  # pylint: disable=broad-except
                logger_no_user_data.error(f'Failed to clean up {network_name}')
                logger.error(exception)

            logger_no_user_data.debug(f'Removed network {network_name} in {time() - network_cleanup_start_time}')

    def _handle_save_job_wrapper(self, package: bytes):
        job_wrapper_json_string = SavedJob(package).deserialize()
        job_wrapper: JobWrapper = json.loads(job_wrapper_json_string)
        BiolibApiClient.initialize(
            base_url=job_wrapper['BASE_URL'],
            access_token=job_wrapper['access_token']
        )
        self._root_job_wrapper = job_wrapper
        if not utils.IS_RUNNING_IN_CLOUD:
            job_wrapper['cloud_job'] = None

        self.job_temporary_dir = job_wrapper['job_temporary_dir']

        job = job_wrapper['job']
        self._jobs[job['public_id']] = job

        app_version = job['app_version']
        modules = app_version.get('modules', [])
        for module in modules:
            module_ports = module.get('ports', [])
            if module_ports:
                logger_no_user_data.debug(
                    f"Job '{job['public_id']}' module '{module['name']}' has ports: {module_ports}"
                )

        if job['app_version'].get('modules') is not None and BiolibDockerClient.is_docker_running():
            self._start_network_and_remote_host_proxies(job)

        # TODO: start downloading runtime zip already at this point

    def _start_network_and_remote_host_proxies(self, job: CreatedJobDict) -> None:
        app_version = job['app_version']
        job_id = job['public_id']
        remote_hosts = app_version['remote_hosts']
        docker_client = BiolibDockerClient.get_docker_client()
        try:
            self._internal_network = docker_client.networks.create(
                name=f'biolib-sandboxed-network-{job_id}',
                internal=True,
                driver='bridge',
            )
        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_CREATE_DOCKER_NETWORKS.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

        if len(remote_hosts) > 0:
            logger_no_user_data.debug(f'Job "{job_id}" starting proxy for remote hosts: {remote_hosts}')
            try:
                hostname_to_ports: Dict[str, List[int]] = {}
                for remote_host in remote_hosts:
                    if ':' in remote_host['hostname']:
                        hostname, port_str = remote_host['hostname'].split(':')
                        port = int(port_str)
                    else:
                        port = 443
                        hostname = remote_host['hostname']

                    if hostname in hostname_to_ports:
                        hostname_to_ports[hostname].append(port)
                    else:
                        hostname_to_ports[hostname] = [port]

                remote_host_mappings: List[RemoteHostMapping] = []
                for hostname, ports in hostname_to_ports.items():
                    network_index = len(remote_host_mappings)
                    subnet = f'172.28.{network_index}.0/24'

                    ipam_pool = IPAMPool(subnet=subnet)
                    ipam_config = IPAMConfig(pool_configs=[ipam_pool])

                    network = docker_client.networks.create(
                        name=f'biolib-remote-host-network-{job_id}-{network_index}',
                        internal=True,
                        driver='bridge',
                        ipam=ipam_config,
                    )

                    static_ip = get_static_ip_from_network(network, offset=2)

                    mapping = RemoteHostMapping(
                        hostname=hostname,
                        ports=ports,
                        network=network,
                        static_ip=static_ip,
                    )
                    remote_host_mappings.append(mapping)
                    logger_no_user_data.debug(
                        f'Created network {network.name} with static IP {static_ip} for host {hostname}'
                    )

                if remote_host_mappings:
                    remote_host_proxy = RemoteHostProxy(
                        remote_host_mappings=remote_host_mappings,
                        job_id=job_id,
                        app_caller_network=None,
                    )
                    remote_host_proxy.start()
                    self._remote_host_proxies.append(remote_host_proxy)
                    num_hosts = len(remote_host_mappings)
                    logger_no_user_data.debug(f'Started single proxy container for {num_hosts} remote hosts')

            except Exception as exception:
                raise ComputeProcessException(
                    exception,
                    SystemExceptionCodes.FAILED_TO_START_REMOTE_HOST_PROXIES.value,
                    self.send_system_exception,
                    may_contain_user_data=False
                ) from exception

        if utils.IS_RUNNING_IN_CLOUD:
            try:
                app_caller_proxy = RemoteHostProxy(
                    remote_host_mappings=[],
                    job_id=job_id,
                    app_caller_network=self._internal_network,
                )
                app_caller_proxy.start()
                self._remote_host_proxies.append(app_caller_proxy)
                logger_no_user_data.debug('Started app caller proxy')
            except Exception as exception:
                raise ComputeProcessException(
                    exception,
                    SystemExceptionCodes.FAILED_TO_START_REMOTE_HOST_PROXIES.value,
                    self.send_system_exception,
                    may_contain_user_data=False
                ) from exception

    def _run_app_version(
            self,
            app_version_id: str,
            module_input_path: str,
            caller_job: CreatedJobDict,
            main_module_output_path: str,
    ) -> None:
        job: CreatedJobDict = BiolibJobApi.create(app_version_id, caller_job=caller_job['public_id'])
        self._jobs[job['public_id']] = job
        self._run_job(job, module_input_path, main_module_output_path)

    def _run_job(self, job: CreatedJobDict, module_input_path: str, main_module_output_path: str) -> None:
        job_uuid = job['public_id']
        logger_no_user_data.info(f'Job "{job_uuid}" running...')
        if self._root_job_wrapper is None:
            raise Exception('root_job_wrapper was None')

        root_job = job
        while root_job['caller_job'] is not None and self._jobs.get(root_job['caller_job']) is not None:
            root_job = self._jobs[root_job['caller_job']]

        root_job_id = root_job['public_id']
        if job.get('arguments_override_command') and not job['app_version']['app']['allow_client_side_execution']:
            raise ComputeProcessException(
                Exception("Command override not allowed"),
                SystemExceptionCodes.COMMAND_OVERRIDE_NOT_ALLOWED.value,
                self.send_system_exception
            )

        modules = job['app_version'].get('modules')
        if not modules:
            raise ComputeProcessException(
                Exception("No modules found on job"),
                SystemExceptionCodes.NO_MODULES_FOUND_ON_JOB.value,
                self.send_system_exception
            )

        main_module = self._get_module_from_name(modules, module_name='main')

        source_files_are_mapped = False
        lfs_dict: Dict[str, LargeFileSystem] = {}
        for module in modules:
            if len(module['source_files_mappings']) > 0:
                source_files_are_mapped = True

            for lfs_mapping in module['large_file_systems']:
                logger_no_user_data.debug(f'Job "{job_uuid}" creating LFS for module "{module["name"]}"...')
                lfs = LargeFileSystem(
                    job_id=job['public_id'],
                    lfs_mapping=lfs_mapping,
                    send_status_update=self._send_status_update,
                )
                logger_no_user_data.debug(f'Job "{job_uuid}" created object for LFS "{lfs.uuid}"')

                lfs.initialize()
                lfs_dict[lfs.uuid] = lfs

        runtime_zip_bytes: Optional[bytes] = None
        if source_files_are_mapped:
            runtime_zip_bytes = self._get_runtime_zip_as_bytes(root_job_id=root_job_id, app_version=job['app_version'])

        self._run_module(
            LocalExecutorOptions(
                access_token=self._root_job_wrapper['access_token'],
                biolib_base_url=self._root_job_wrapper['BASE_URL'],
                compute_node_info=self._root_job_wrapper.get('compute_node_info'),
                internal_network=self._internal_network,
                job=job,
                cloud_job=self._root_job_wrapper['cloud_job'],
                large_file_systems=lfs_dict,
                module=main_module,
                module_input_path=module_input_path,
                module_output_path=main_module_output_path,
                remote_host_proxies=self._remote_host_proxies,
                root_job_id=root_job_id,
                runtime_zip_bytes=runtime_zip_bytes,
                send_status_update=self._send_status_update,
                send_system_exception=self.send_system_exception,
                send_stdout_and_stderr=self.send_stdout_and_stderr,
            )
        )

        if utils.IS_RUNNING_IN_CLOUD:
            # Log memory and disk after pulling and executing module
            log_disk_and_memory_usage_info()

    def _run_module(
            self,
            options: LocalExecutorOptions,
    ) -> None:
        module = options['module']
        job_id = options['job']['public_id']
        module_output_path = options['module_output_path']
        module_input_path = options['module_input_path']
        logger_no_user_data.debug(f'Job "{job_id}" running module "{module["name"]}"...')

        executor_instance: DockerExecutor
        if module['environment'] == ModuleEnvironment.BIOLIB_APP.value:
            if not self.job_temporary_dir:
                raise BioLibError('Undefined job_temporary_dir')
            logger_no_user_data.debug(f'Job "{job_id}" starting child job...')
            with open(module_input_path,'rb') as fp:
                module_input_serialized = fp.read()
            module_input = ModuleInput(module_input_serialized).deserialize()
            module_input_with_runtime_zip = self._add_runtime_zip_and_command_to_module_input(options, module_input)
            module_input_with_runtime_zip_serialized = ModuleInput().serialize(
                stdin=module_input_with_runtime_zip['stdin'],
                arguments=module_input_with_runtime_zip['arguments'],
                files=module_input_with_runtime_zip['files'],
            )
            module_input_path_new = os.path.join(self.job_temporary_dir, "runtime." + JobStorage.module_input_file_name)
            open(module_input_path_new, 'wb').write(module_input_with_runtime_zip_serialized)
            return self._run_app_version(
                module['image_uri'],
                module_input_path_new,
                options['job'],
                module_output_path,
            )

        elif module['environment'] == ModuleEnvironment.BIOLIB_ECR.value and BiolibDockerClient.is_docker_running():
            try:
                executor_instance = DockerExecutor(options)
            except Exception as exception:
                raise ComputeProcessException(
                    exception,
                    SystemExceptionCodes.FAILED_TO_INITIALIZE_DOCKER_EXECUTOR.value,
                    self.send_system_exception,
                    may_contain_user_data=False
                ) from exception
        else:
            err_string = f'Job "{job_id}" hit unsupported module environment "{module["environment"]}"'
            logger_no_user_data.error(err_string)
            raise Exception(err_string)

        self._executors.append(executor_instance)

        if utils.IS_RUNNING_IN_CLOUD:
            # Log memory and disk before pulling and executing module
            log_disk_and_memory_usage_info()

        executor_instance.execute_module()

    def _connect_to_parent(self):
        try:
            parent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            parent_socket.connect((SOCKET_HOST, int(self._socket_port)))

        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_CONNECT_TO_WORKER_THREAD_SOCKET.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

        try:
            SocketListenerThread(parent_socket, self._received_messages_queue).start()
            SocketSenderThread(parent_socket, self._messages_to_send_queue).start()
        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_START_SENDER_THREAD_OR_RECEIVER_THREAD.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

    # TODO: move this mapping logic to the ModuleInput class
    def _add_runtime_zip_and_command_to_module_input(self, options: LocalExecutorOptions, module_input):
        module = options['module']
        runtime_zip_byes = options['runtime_zip_bytes']
        # TODO: Figure out if we ever forward output mappings correctly (Do we only the mapping of the base image?)
        # TODO: Reuse much of the make_runtime_tar logic in BiolibDockerClient
        try:
            if runtime_zip_byes:
                runtime_zip = zipfile.ZipFile(io.BytesIO(runtime_zip_byes))
                source_mappings = Mappings(module['source_files_mappings'], module_input['arguments'])
                for zip_file_name in runtime_zip.namelist():
                    file_path = '/' + path_without_first_folder(zip_file_name)
                    mapped_file_names = source_mappings.get_mappings_for_path(file_path)
                    for mapped_file_name in mapped_file_names:
                        file_data = runtime_zip.read(zip_file_name)
                        module_input['files'].update({mapped_file_name: file_data})

            for command_part in reversed(shlex.split(module['command'])):
                module_input['arguments'].insert(0, command_part)

        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_CREATE_NEW_JOB.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

        return module_input

    def _get_runtime_zip_as_bytes(self, root_job_id: str, app_version: AppVersionOnJob) -> Optional[bytes]:
        runtime_zip_url = app_version['client_side_executable_zip']

        # TODO: change this to a is None check when backend is fixed to not return empty string
        if not runtime_zip_url:
            return None

        runtime_zip_bytes: Optional[bytes] = self._app_version_id_to_runtime_zip.get(app_version['public_id'])

        if runtime_zip_bytes is None:
            self._send_status_update(StatusUpdate(progress=25, log_message='Downloading Source Files...'))

            start_time = time()
            logger_no_user_data.debug(f'Job "{root_job_id}" downloading runtime zip...')
            try:
                runtime_zip_bytes = HttpClient.request(url=runtime_zip_url).content
            except Exception as exception:
                raise ComputeProcessException(
                    exception,
                    SystemExceptionCodes.FAILED_TO_DOWNLOAD_RUNTIME_ZIP.value,
                    self.send_system_exception,
                    may_contain_user_data=False
                ) from exception
            finally:
                download_time = time() - start_time
                logger_no_user_data.debug(f'Job "{root_job_id}" download of runtime zip took: {download_time}s')

            self._app_version_id_to_runtime_zip[app_version['public_id']] = runtime_zip_bytes

        return runtime_zip_bytes

    @staticmethod
    def _get_module_from_name(modules: List[Module], module_name: str):
        for module in modules:
            if module['name'] == module_name:
                return module
        raise Exception(f'Could not find module with name {module_name}')

    def send_system_exception(self, biolib_exception_code: int) -> None:
        system_exception_string = SystemExceptionCodeMap.get(biolib_exception_code)
        logger_no_user_data.error(f'Hit system exception: {system_exception_string} ({biolib_exception_code})')

        system_exception_package = SystemException().serialize(biolib_exception_code)
        self._messages_to_send_queue.put(system_exception_package)

    def send_stdout_and_stderr(self, stdout_and_stderr_bytes: bytes) -> None:
        if utils.IS_RUNNING_IN_CLOUD:
            stdout_and_stderr_package = StdoutAndStderr().serialize(stdout_and_stderr_bytes=stdout_and_stderr_bytes)
            self._messages_to_send_queue.put(stdout_and_stderr_package)
        else:
            sys.stdout.write(stdout_and_stderr_bytes.decode())
            if not utils.IS_RUNNING_IN_NOTEBOOK:  # for some reason flushing in jupyter notebooks breaks \r handling
                sys.stdout.flush()

    def _send_status_update(self, status_update: StatusUpdate) -> None:
        try:
            status_update_package = SystemStatusUpdate().serialize(
                status_update['progress'],
                status_update['log_message'],
            )
            logger.debug(status_update['log_message'])
            self._messages_to_send_queue.put(status_update_package)
        except Exception as exception:
            raise ComputeProcessException(
                exception,
                SystemExceptionCodes.FAILED_TO_SEND_STATUS_UPDATE.value,
                self.send_system_exception,
                may_contain_user_data=False
            ) from exception

    def _run_root_job(self, module_input_path: str) -> str:
        # Make typechecker happy
        if not self._root_job_wrapper or not self.job_temporary_dir:
            raise BioLibError('Undefined job_wrapper or job_temporary_dir')

        main_module_output_path = os.path.join(self.job_temporary_dir, JobStorage.module_output_file_name)
        self._run_job(
            job=self._root_job_wrapper['job'],
            module_input_path=module_input_path,
            main_module_output_path=main_module_output_path,
        )
        self._send_status_update(StatusUpdate(progress=94, log_message='Computation finished'))
        return main_module_output_path

    def run_job_locally(self, job_dict: CreatedJobDict, module_input_serialized: bytes) -> ModuleOutputV2:
        try:
            with tempfile.TemporaryDirectory() as job_temporary_dir:
                self.job_temporary_dir = job_temporary_dir
                self._root_job_wrapper = JobWrapper(
                    access_token=BiolibApiClient.get().access_token or '',
                    BASE_URL=BiolibApiClient.get().base_url,
                    cloud_job=None,
                    compute_node_info=None,
                    job=job_dict,
                    job_temporary_dir=job_temporary_dir,
                )
                self._start_network_and_remote_host_proxies(job_dict)
                module_input_path = os.path.join(self.job_temporary_dir, JobStorage.module_input_file_name)
                open(module_input_path, 'wb').write(module_input_serialized)
                module_output_path = self._run_root_job(module_input_path)
                with open(module_output_path, mode='rb') as module_output_file:
                    module_output_serialized = module_output_file.read()
                return ModuleOutputV2(InMemoryIndexableBuffer(module_output_serialized))
        finally:
            self._cleanup()
