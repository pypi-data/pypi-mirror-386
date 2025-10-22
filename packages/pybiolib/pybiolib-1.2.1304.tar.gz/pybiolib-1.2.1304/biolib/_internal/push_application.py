import json
import os
import re
import sys
import time
from pathlib import Path

import rich.progress
import yaml

from biolib import api, utils
from biolib._internal.data_record.push_data import (
    push_data_path,
    validate_data_path_and_get_files_and_size_of_directory,
)
from biolib._internal.errors import AuthenticationError
from biolib._internal.file_utils import get_files_and_size_of_directory, get_iterable_zip_stream
from biolib._internal.types.push import PushResponseDict
from biolib.biolib_api_client import BiolibApiClient
from biolib.biolib_api_client.biolib_app_api import BiolibAppApi
from biolib.biolib_docker_client import BiolibDockerClient
from biolib.biolib_errors import BioLibError
from biolib.biolib_logging import logger
from biolib.typing_utils import Iterable, Optional, Set, TypedDict
from biolib.utils.app_uri import parse_app_uri

REGEX_MARKDOWN_INLINE_IMAGE = re.compile(r'!\[(?P<alt>.*)\]\((?P<src>.*)\)')


class DockerProgressDetail(TypedDict):
    current: int
    total: int


class DockerStatusUpdate(TypedDict, total=False):
    status: str
    progressDetail: DockerProgressDetail
    progress: str
    id: str


def process_docker_status_updates(status_updates: Iterable[DockerStatusUpdate], action: str) -> None:
    if sys.stdout.isatty():
        _process_docker_status_updates_with_progress_bar(status_updates, action)
    else:
        _process_docker_status_updates_with_logging(status_updates, action)


def _process_docker_status_updates_with_progress_bar(status_updates: Iterable[DockerStatusUpdate], action: str) -> None:
    with rich.progress.Progress() as progress:
        layer_id_to_task_id = {}
        overall_task_id = progress.add_task(description=f'[bold blue]{action} Docker image', total=None)

        for update in status_updates:
            if 'progressDetail' in update and 'id' in update:
                layer_id = update['id']
                progress_detail = update['progressDetail']

                if layer_id not in layer_id_to_task_id:
                    layer_id_to_task_id[layer_id] = progress.add_task(description=f'[cyan]{action} layer {layer_id}')

                if progress_detail and 'current' in progress_detail and 'total' in progress_detail:
                    progress.update(
                        task_id=layer_id_to_task_id[layer_id],
                        completed=progress_detail['current'],
                        total=progress_detail['total'],
                    )
                elif update['status'] == 'Layer already exists':
                    progress.update(
                        completed=100,
                        task_id=layer_id_to_task_id[layer_id],
                        total=100,
                    )
            elif 'status' in update and 'id' in update:
                layer_id = update['id']
                status = update['status']

                if layer_id not in layer_id_to_task_id:
                    layer_id_to_task_id[layer_id] = progress.add_task(description=f'[cyan]{action} layer {layer_id}')

                if status in ['Preparing', 'Waiting']:
                    progress.update(
                        task_id=layer_id_to_task_id[layer_id], description=f'[yellow]{status} layer {layer_id}'
                    )
                elif status in ['Pushing', 'Uploading']:
                    progress.update(
                        task_id=layer_id_to_task_id[layer_id], description=f'[cyan]{status} layer {layer_id}'
                    )
                elif status in ['Pushed', 'Uploaded']:
                    progress.update(
                        task_id=layer_id_to_task_id[layer_id],
                        description=f'[green]{status} layer {layer_id}',
                        completed=100,
                        total=100,
                    )
                elif status == 'Layer already exists':
                    progress.update(
                        task_id=layer_id_to_task_id[layer_id],
                        description=f'[green]{status} - layer {layer_id}',
                        completed=100,
                        total=100,
                    )
            elif 'status' in update and update['status']:
                status = update['status']
                if status not in ['Preparing', 'Pushing', 'Pushed', 'Waiting', 'Layer already exists']:
                    progress.update(task_id=overall_task_id, description=f'[bold blue]{action} Docker image - {status}')
            elif 'status' not in update and 'progressDetail' not in update:
                print(update)


def _process_docker_status_updates_with_logging(status_updates: Iterable[DockerStatusUpdate], action: str) -> None:
    layer_progress = {}
    layer_status = {}
    last_log_time = time.time()

    logger.info(f'{action} Docker image...')

    for update in status_updates:
        current_time = time.time()

        if 'progressDetail' in update and 'id' in update:
            layer_id = update['id']
            progress_detail = update['progressDetail']

            if progress_detail and 'current' in progress_detail and 'total' in progress_detail:
                current = progress_detail['current']
                total = progress_detail['total']
                percentage = (current / total * 100) if total > 0 else 0
                layer_progress[layer_id] = percentage
                layer_status[layer_id] = f'{action.lower()}'
            elif update.get('status') == 'Layer already exists':
                layer_progress[layer_id] = 100
                layer_status[layer_id] = 'already exists'

        elif 'status' in update and 'id' in update:
            layer_id = update['id']
            status = update['status']
            layer_status[layer_id] = status.lower()

            if status in ['Pushed', 'Uploaded'] or status == 'Layer already exists':
                layer_progress[layer_id] = 100

        elif 'status' in update and update['status']:
            status = update['status']
            if status not in ['Preparing', 'Pushing', 'Pushed', 'Waiting', 'Layer already exists']:
                logger.info(f'{action} Docker image - {status}')

        if current_time - last_log_time >= 10.0:
            _log_progress_summary(action, layer_progress, layer_status)
            last_log_time = current_time

    _log_progress_summary(action, layer_progress, layer_status)
    if action == 'Pushing':
        logger.info('Pushing final image manifest...')
    logger.info(f'{action} Docker image completed')


def _log_progress_summary(action: str, layer_progress: dict, layer_status: dict) -> None:
    if not layer_progress and not layer_status:
        return

    completed_layers = sum(1 for progress in layer_progress.values() if progress >= 100)
    total_layers = len(layer_progress) if layer_progress else len(layer_status)

    if total_layers > 0:
        overall_percentage = completed_layers / total_layers * 100
        logger.info(
            f'{action} progress: {completed_layers}/{total_layers} layers completed ({overall_percentage:.1f}%)'
        )

    active_layers = [
        layer_id
        for layer_id, status in layer_status.items()
        if status in ['preparing', 'waiting', 'pushing', 'uploading'] and layer_progress.get(layer_id, 0) < 100
    ]

    if active_layers:
        logger.info(f'Active layers: {", ".join(active_layers[:5])}{"..." if len(active_layers) > 5 else ""}')


def set_app_version_as_active(
    app_version_uuid: str,
):
    logger.debug(f'Setting app version {app_version_uuid} as active.')
    api.client.patch(
        path=f'/app_versions/{app_version_uuid}/',
        data={'set_as_active': True},
    )


def push_application(
    app_uri: str,
    app_path: str,
    app_version_to_copy_images_from: Optional[str],
    set_as_active: bool,
    set_as_published: bool,
    dry_run: bool = False,
) -> Optional[PushResponseDict]:
    parsed_uri = parse_app_uri(app_uri)
    app_name = parsed_uri['app_name']

    app_uri_prefix = (
        f"@{parsed_uri['resource_name_prefix']}/" if parsed_uri['resource_name_prefix'] != 'biolib.com' else ''
    )
    app_uri_to_fetch = f"{app_uri_prefix}{parsed_uri['account_handle_normalized']}/{app_name}"

    version = parsed_uri['version']
    semantic_version = f"{version['major']}.{version['minor']}.{version['patch']}" if version else None

    app_path_absolute = Path(app_path).resolve()

    api_client = BiolibApiClient.get()
    if not api_client.is_signed_in:
        github_repository = os.getenv('GITHUB_REPOSITORY')
        if github_repository and not api_client.resource_deploy_key:
            github_secrets_url = f'https://github.com/{github_repository}/settings/secrets/actions/new'
            raise AuthenticationError(
                'You must be authenticated to push an application.\n'
                'Please set the environment variable "BIOLIB_TOKEN=[your_deploy_token]"\n'
                f'You can get a deploy key at: {api_client.base_url}/{app_uri_to_fetch}/settings/keys/\n'
                f'Then add it to your GitHub repository at: {github_secrets_url}'
            )
        else:
            raise AuthenticationError(
                'You must be authenticated to push an application.\n'
                'Please set the environment variable "BIOLIB_TOKEN=[your_deploy_token]"\n'
                f'You can get a deploy key at: {api_client.base_url}/{app_uri_to_fetch}/settings/keys/'
            )

    # prepare zip file
    config_yml_path = app_path_absolute.joinpath('.biolib/config.yml')
    if not config_yml_path.is_file():
        raise BioLibError('The file .biolib/config.yml was not found in the application directory')

    zip_filters: Set[str] = set()
    zip_filters.add('.biolib/config.yml')

    input_files_maps_to_root = False
    app_data_path: Optional[Path] = None
    try:
        with open(config_yml_path) as config_yml_file:
            try:
                config = json.loads(json.dumps(yaml.safe_load(config_yml_file.read())))
            except (TypeError, ValueError) as e:
                raise BioLibError(
                    f'The .biolib/config.yml file contains data types that are not supported '
                    f'(must be JSON-serializable). Please ensure only standard JSON types '
                    f'(str, int, float, bool, list, dict, null) are used. Original error: {e}'
                ) from e

        if 'assets' in config and 'app_data' not in config:
            config['app_data'] = config.pop('assets')
        elif 'assets' in config and 'app_data' in config:
            raise BioLibError(
                'In .biolib/config.yml you cannot specify both "app_data" and "assets" fields. Please use only one.'
            )

        app_data = config.get('app_data')
        if app_data:
            field_name = 'app_data' if 'app_data' in config else 'assets'
            if not isinstance(app_data, str):
                raise BioLibError(
                    f'In .biolib/config.yml the value of "{field_name}" must be a string but got {type(app_data)}'
                )

            app_data_path = app_path_absolute.joinpath(app_data).resolve()
            if not app_data_path.is_dir():
                raise BioLibError(
                    f'In .biolib/config.yml the value of "{field_name}" must be a path to a directory '
                    'in the application directory'
                )

        license_file_relative_path = config.get('license_file', 'LICENSE')
        if app_path_absolute.joinpath(license_file_relative_path).is_file():
            zip_filters.add(license_file_relative_path)

        description_file_relative_path = config.get('description_file', 'README.md')
        description_file_absolute_path = app_path_absolute.joinpath(description_file_relative_path)
        if not description_file_absolute_path.is_file():
            raise BioLibError(f'Could not find {description_file_relative_path}')

        zip_filters.add(description_file_relative_path)
        with open(description_file_absolute_path) as description_file:
            description_file_content = description_file.read()

        for _, img_src_path in re.findall(REGEX_MARKDOWN_INLINE_IMAGE, description_file_content):
            zip_filters.add(img_src_path)

        for _, module in config['modules'].items():
            if module.get('source_files'):
                zip_filters.add('*')

            for mapping in module.get('input_files', []):
                mapping_parts = mapping.split(' ')
                if len(mapping_parts) == 3 and mapping_parts[2] == '/':
                    input_files_maps_to_root = True

    except BioLibError as error:
        raise error from None

    except Exception as error:
        raise BioLibError('Failed to parse the .biolib/config.yml file') from error

    if input_files_maps_to_root:
        logger.error(
            'Error: In your config.yml some module maps input files to "/" (root). '
            'This is potentially an unsafe operation as it allows the user to '
            'overwrite system executables in the module.'
        )
        exit(1)

    files_in_app_dir, _ = get_files_and_size_of_directory(directory=str(app_path_absolute))
    files_to_zip: Set[str] = set()

    for file_path in files_in_app_dir:
        for pattern in zip_filters:
            if pattern == '*' or pattern == file_path:
                files_to_zip.add(file_path)
                break

    original_directory = os.getcwd()
    os.chdir(app_path_absolute.parent)
    files_with_app_dir_prefixed = [f'{app_path_absolute.stem}/{path}' for path in files_to_zip]

    # Workaround as backend currently expects directory objects for root level and .biolib directory
    files_with_app_dir_prefixed.append(f'{app_path_absolute.stem}/')
    files_with_app_dir_prefixed.append(f'{app_path_absolute.stem}/.biolib/')

    byte_iterator = get_iterable_zip_stream(files_with_app_dir_prefixed, chunk_size=50_000_000)
    source_files_zip_bytes = b''.join(byte_iterator)
    os.chdir(original_directory)

    if app_version_to_copy_images_from and app_version_to_copy_images_from != 'active':
        # Get app with `app_version_to_copy_images_from` in app_uri_to_fetch to get the app version public id.
        app_uri_to_fetch += f':{app_version_to_copy_images_from}'

    app_response = BiolibAppApi.get_by_uri(app_uri_to_fetch)
    app = app_response['app']

    if app_data and not app['allow_client_side_execution'] and 'app_data' in config:
        raise BioLibError(
            'To push a version with app_data the app must be set to "Allow Client-Side Source Code Access"'
        )
    if dry_run:
        logger.info('Successfully completed dry-run. No new version was pushed.')
        return None

    new_app_version_json = BiolibAppApi.push_app_version(
        semantic_version=semantic_version,
        app_id=app['public_id'],
        app_name=app['name'],
        author=app['account_handle'],
        set_as_active=False,
        zip_binary=source_files_zip_bytes,
        app_version_id_to_copy_images_from=app_response['app_version']['public_id']
        if app_version_to_copy_images_from
        else None,
    )

    if app_data_path:
        app_data_files_to_zip, app_data_size_in_bytes = validate_data_path_and_get_files_and_size_of_directory(
            data_path=str(app_data_path),
        )
        push_data_path(
            resource_version_uuid=new_app_version_json['public_id'],
            data_path=str(app_data_path),
            data_size_in_bytes=app_data_size_in_bytes,
            files_to_zip=app_data_files_to_zip,
        )

    #  Don't push docker images if copying from another app version
    docker_tags = new_app_version_json.get('docker_tags', {})
    if not app_version_to_copy_images_from and docker_tags:
        logger.info('Found docker images to push.')
        docker_client = BiolibDockerClient.get_docker_client()

        for module_name, repo_and_tag in docker_tags.items():
            docker_image_definition = config['modules'][module_name]['image']
            repo, tag = repo_and_tag.split(':')

            if docker_image_definition.startswith('dockerhub://'):
                docker_image_name = docker_image_definition.replace('dockerhub://', 'docker.io/', 1)
                logger.info(f'Pulling image {docker_image_name} defined on module {module_name} from Dockerhub.')
                dockerhub_repo, dockerhub_tag = docker_image_name.split(':')
                pull_status_updates: Iterable[DockerStatusUpdate] = docker_client.api.pull(
                    decode=True,
                    platform='linux/amd64',
                    repository=dockerhub_repo,
                    stream=True,
                    tag=dockerhub_tag,
                )

                process_docker_status_updates(pull_status_updates, action='Pulling')

            elif docker_image_definition.startswith('local-docker://'):
                docker_image_name = docker_image_definition.replace('local-docker://', '', 1)

            try:
                logger.info(f'Trying to push image {docker_image_name} defined on module {module_name}.')
                image = docker_client.images.get(docker_image_name)
                architecture = image.attrs.get('Architecture')
                if architecture != 'amd64':
                    print(f"Error: '{docker_image_name}' is compiled for {architecture}, expected x86 (amd64).")
                    print('If you are on an ARM processor, try passing --platform linux/amd64 to docker build.')
                    exit(1)
                absolute_repo_uri = f'{utils.BIOLIB_SITE_HOSTNAME}/{repo}'
                image.tag(absolute_repo_uri, tag)

                push_status_updates: Iterable[DockerStatusUpdate] = docker_client.images.push(
                    absolute_repo_uri,
                    tag=tag,
                    stream=True,
                    decode=True,
                    auth_config={
                        'username': 'biolib',
                        # For legacy reasons access token is sent with trailing comma ','
                        'password': api_client.resource_deploy_key or f'{api_client.access_token},',
                    },
                )

                process_docker_status_updates(push_status_updates, action='Pushing')

            except Exception as exception:
                raise BioLibError(f'Failed to tag and push image {docker_image_name}.') from exception

            logger.info(f'Successfully pushed {docker_image_name}')

    app_version_uuid = new_app_version_json['public_id']
    api.client.post(
        path=f'/app-versions/{app_version_uuid}/complete-push/',
        data={'set_as_active': set_as_active, 'set_as_published': set_as_published},
    )

    sematic_version = f"{new_app_version_json['major']}.{new_app_version_json['minor']}.{new_app_version_json['patch']}"
    version_name = 'development ' if not set_as_published else ''
    logger.info(f'Successfully pushed new {version_name}version {sematic_version} of {app_uri}.')

    return {'app_uri': app_uri, 'sematic_version': sematic_version}
