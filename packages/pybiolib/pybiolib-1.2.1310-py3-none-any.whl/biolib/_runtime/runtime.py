import json
import re
from pathlib import Path
from typing import Optional

from biolib import api
from biolib._internal.runtime import BioLibRuntimeError, BioLibRuntimeNotRecognizedError, RuntimeJobDataDict
from biolib.biolib_logging import logger
from biolib.typing_utils import cast
from biolib.utils.seq_util import SeqUtil


class Runtime:
    _job_data: Optional[RuntimeJobDataDict] = None

    @staticmethod
    def check_is_environment_biolib_app() -> bool:
        return bool(Runtime._try_to_get_job_data())

    @staticmethod
    def check_is_environment_biolib_cloud() -> bool:
        return Runtime._get_job_data().get('is_environment_biolib_cloud', False)

    @staticmethod
    def get_job_id() -> str:
        return Runtime._get_job_data()['job_uuid']

    @staticmethod
    def get_job_auth_token() -> str:
        return Runtime._get_job_data()['job_auth_token']

    @staticmethod
    def get_job_requested_machine() -> Optional[str]:
        job_data = Runtime._get_job_data()
        job_requested_machine = job_data.get('job_requested_machine')
        if not job_requested_machine:
            return None
        return job_requested_machine

    @staticmethod
    def get_app_uri() -> str:
        return Runtime._get_job_data()['app_uri']

    @staticmethod
    def get_max_workers() -> int:
        return Runtime._get_job_data()['job_reserved_machines']

    @staticmethod
    def get_secret(secret_name: str) -> bytes:
        assert re.match(
            '^[a-zA-Z0-9_-]*$', secret_name
        ), 'Secret name can only contain alphanumeric characters and dashes or underscores '
        try:
            with open(f'/biolib/secrets/{secret_name}', 'rb') as file:
                return file.read()
        except BaseException as error:
            raise BioLibRuntimeError(f'Unable to get system secret: {secret_name}') from error

    @staticmethod
    def get_temporary_client_secret(secret_name: str) -> bytes:
        assert re.match(
            '^[a-zA-Z0-9_-]*$', secret_name
        ), 'Secret name can only contain alphanumeric characters and dashes or underscores '
        try:
            with open(f'/biolib/temporary-client-secrets/{secret_name}', 'rb') as file:
                return file.read()
        except BaseException as error:
            raise BioLibRuntimeError(f'Unable to get secret: {secret_name}') from error

    @staticmethod
    def set_main_result_prefix(result_prefix: str) -> None:
        job_data = Runtime._get_job_data()
        api.client.patch(
            data={'result_name_prefix': result_prefix},
            headers={'Job-Auth-Token': job_data['job_auth_token']},
            path=f"/jobs/{job_data['job_uuid']}/main_result/",
        )

    @staticmethod
    def set_result_name_prefix(result_prefix: str) -> None:
        Runtime.set_main_result_prefix(result_prefix)

    @staticmethod
    def set_result_name_prefix_from_fasta(path_to_fasta: str) -> None:
        """
        Set BioLib result name to FASTA file name (excluding file extension) or,
        if detecting a BioLib generated name, use ID of the first sequence in the fasta file
        """
        try:
            # Set job name to first header if FASTA text input (random BioLib file) detected
            if re.match('^input_[A-Za-z0-9]+.*', path_to_fasta):
                first_id = next(SeqUtil.parse_fasta(path_to_fasta)).id
                result_name = first_id.replace(' ', '_')[:60]
            else:
                result_name = Path(path_to_fasta).name

            logger.debug(f'Setting result name to "{result_name}" from {path_to_fasta}')
            Runtime.set_result_name_prefix(result_name)
        except Exception as e:
            logger.warning(f'Failed to set result name from fasta file {path_to_fasta}: {str(e)}')

    @staticmethod
    def set_result_name_from_file(path_to_file: str) -> None:
        try:
            if path_to_file.lower().endswith('.fasta'):
                return Runtime.set_result_name_prefix_from_fasta(path_to_file)

            # Set job name only if not a BioLib default name
            if not re.match('^input_[A-Za-z0-9]+.*', path_to_file):
                result_name = Path(path_to_file).name[:60]
                logger.debug(f'Setting result name to "{result_name}" from {path_to_file}')
                Runtime.set_result_name_prefix(result_name)
        except Exception as e:
            logger.warning(f'Failed to set result name from file {path_to_file}: {str(e)}')

    @staticmethod
    def set_result_name_from_string(result_name: str) -> None:
        try:
            truncated_name = result_name[:60]
            logger.debug(f'Setting result name to "{truncated_name}" from string')
            Runtime.set_result_name_prefix(truncated_name)
        except Exception as e:
            logger.warning(f'Failed to set result name from string: {str(e)}')

    @staticmethod
    def create_result_note(note: str) -> None:
        job_id = Runtime.get_job_id()
        # Note: Authentication is added by app caller proxy in compute node
        api.client.post(data={'note': note}, path=f'/jobs/{job_id}/notes/')

    @staticmethod
    def _try_to_get_job_data() -> Optional[RuntimeJobDataDict]:
        if not Runtime._job_data:
            try:
                with open('/biolib/secrets/biolib_system_secret') as file:
                    job_data: RuntimeJobDataDict = json.load(file)
            except BaseException:
                return None

            if not job_data['version'].startswith('1.'):
                raise BioLibRuntimeError(f"Unexpected system secret version {job_data['version']} expected 1.x.x")

            Runtime._job_data = job_data

        return cast(RuntimeJobDataDict, Runtime._job_data)

    @staticmethod
    def _get_job_data() -> RuntimeJobDataDict:
        job_data = Runtime._try_to_get_job_data()
        if not job_data:
            raise BioLibRuntimeNotRecognizedError() from None
        return job_data
