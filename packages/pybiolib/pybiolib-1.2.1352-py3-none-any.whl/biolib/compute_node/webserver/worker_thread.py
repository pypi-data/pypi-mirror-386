import base64
import os
import random
import shutil
import socket
import sys
import threading
import time
from queue import Queue
from typing import Optional

from biolib import api, utils
from biolib.biolib_binary_format import ModuleOutputV2, SystemException, SystemStatusUpdate
from biolib.biolib_binary_format.utils import LocalFileIndexableBuffer
from biolib.biolib_logging import logger, logger_no_user_data
from biolib.compute_node.cloud_utils import CloudUtils
from biolib.compute_node.job_worker import JobWorkerProcess
from biolib.compute_node.job_worker.job_storage import JobStorage
from biolib.compute_node.socker_listener_thread import SocketListenerThread
from biolib.compute_node.socket_sender_thread import SocketSenderThread
from biolib.compute_node.utils import SystemExceptionCodes, WorkerThreadException, get_package_type
from biolib.compute_node.webserver import webserver_utils

SOCKET_HOST = '127.0.0.1'


class WorkerThread(threading.Thread):
    def __init__(self, compute_state):
        try:
            super().__init__()
            self.compute_state = compute_state
            self._socket_port = random.choice(range(6000, 65000))
            self._socket = None
            self._connection = None
            self._job_worker_process = None
            self._connection_thread = None
            self._listener_thread = None
            self._sender_thread = None
            self._start_and_connect_to_compute_process()

            logger.debug(f'WorkerThread connected to port {self._socket_port}')

        except Exception as exception:
            logger_no_user_data.error(exception)
            raise WorkerThreadException(
                exception,
                SystemExceptionCodes.FAILED_TO_INITIALIZE_WORKER_THREAD.value,
                worker_thread=self,
            ) from exception

    @property
    def _job_uuid(self):
        return self.compute_state['job_id']

    @property
    def _job_temporary_dir(self):
        return self.compute_state['job_temporary_dir']

    def _upload_module_output_and_get_exit_code(self) -> Optional[int]:
        exit_code = None
        try:
            module_output_path = os.path.join(
                self._job_temporary_dir,
                JobStorage.module_output_file_name,
            )
            if os.path.exists(module_output_path):
                module_output = ModuleOutputV2(buffer=LocalFileIndexableBuffer(filename=module_output_path))
                exit_code = module_output.get_exit_code()
                logger_no_user_data.debug(f'Got exit code: {exit_code}')
                if utils.IS_RUNNING_IN_CLOUD:
                    JobStorage.upload_module_output(
                        job_temporary_dir=self._job_temporary_dir,
                        job_uuid=self._job_uuid,
                    )
        except Exception as error:
            logger_no_user_data.error(f'Could not upload module output or get exit code: {error}')
        return exit_code

    def run(self):
        try:
            while True:
                package = self.compute_state['received_messages_queue'].get()
                if package == b'CANCEL_JOB':
                    logger_no_user_data.info(f'Job "{self._job_uuid}" got cancel signal')
                    self.compute_state['status']['error_code'] = SystemExceptionCodes.CANCELLED_BY_USER.value
                    self.terminate()

                package_type = get_package_type(package)

                if package_type == 'StdoutAndStderr':
                    self.compute_state['status']['stdout_and_stderr_packages_b64'].append(
                        base64.b64encode(package).decode()
                    )

                elif package_type == 'SystemStatusUpdate':
                    progress, log_message = SystemStatusUpdate(package).deserialize()
                    self._set_status_update(progress, log_message)

                    # If 'Computation Finished'
                    if progress == 94:
                        self.compute_state['exit_code'] = self._upload_module_output_and_get_exit_code()
                        self._set_status_update(progress=95, log_message='Result Ready')
                        self.compute_state['is_completed'] = True
                        self.terminate()

                elif package_type == 'SystemException':
                    error_code = SystemException(package).deserialize()
                    self.compute_state['status']['error_code'] = error_code
                    logger.debug('Hit error. Terminating Worker Thread and Compute Process')
                    self.compute_state['progress'] = 95
                    self.terminate()

                elif package_type == 'AesEncryptedPackage':
                    if self.compute_state['progress'] == 94:  # Check if encrypted package is ModuleOutput
                        self.compute_state['result'] = package
                        self.terminate()
                    else:  # Else it is StdoutAndStderr
                        self.compute_state['status']['stdout_and_stderr_packages_b64'].append(
                            base64.b64encode(package).decode()
                        )

                else:
                    raise Exception(f'Package type from child was not recognized: {package}')

                self.compute_state['received_messages_queue'].task_done()

        except Exception as exception:
            raise WorkerThreadException(
                exception,
                SystemExceptionCodes.FAILED_TO_HANDLE_PACKAGE_IN_WORKER_THREAD.value,
                worker_thread=self,
            ) from exception

    def _set_status_update(self, progress: int, log_message: str) -> None:
        status_update = dict(progress=progress, log_message=log_message)
        logger_no_user_data.debug(f'Job "{self._job_uuid}" got system log: {status_update}')

        self.compute_state['progress'] = progress
        self.compute_state['status']['status_updates'].append(status_update)

    def _start_and_connect_to_compute_process(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger_no_user_data.debug(f'Trying to bind to socket on {SOCKET_HOST}:{self._socket_port}')
        self._socket.bind((SOCKET_HOST, self._socket_port))

        logger_no_user_data.debug(f'Starting to listen to socket on port {self._socket_port}')
        self._socket.listen()
        logger_no_user_data.debug(f'Listening to port {self._socket_port}')

        received_messages_queue = Queue()
        messages_to_send_queue = Queue()

        # Starting a thread for accepting connections before starting the process that should to connect to the socket
        logger_no_user_data.debug('Starting connection thread')
        self._connection_thread = threading.Thread(
            target=self._accept_new_socket_connection,
            args=[received_messages_queue, messages_to_send_queue],
        )
        self._connection_thread.start()
        logger_no_user_data.debug('Started connection thread')
        logger_no_user_data.debug('Starting compute process')

        self._job_worker_process = JobWorkerProcess(socket_port=self._socket_port, log_level=logger.level)
        self._job_worker_process.start()

        self.compute_state['received_messages_queue'] = received_messages_queue
        self.compute_state['messages_to_send_queue'] = messages_to_send_queue
        self.compute_state['worker_thread'] = self

    def _accept_new_socket_connection(self, received_messages_queue, messages_to_send_queue):
        self._connection, _ = self._socket.accept()
        self._listener_thread = SocketListenerThread(self._connection, received_messages_queue)
        self._listener_thread.start()

        self._sender_thread = SocketSenderThread(self._connection, messages_to_send_queue)
        self._sender_thread.start()

    def terminate(self) -> None:
        cloud_job_uuid = self.compute_state['cloud_job_id']
        system_exception_code = self.compute_state['status'].get('error_code')

        if utils.IS_RUNNING_IN_CLOUD and system_exception_code not in [
            SystemExceptionCodes.CANCELLED_BY_USER.value,
            SystemExceptionCodes.EXCEEDED_MAX_JOB_RUNTIME.value,
        ]:
            CloudUtils.finish_cloud_job(
                cloud_job_id=cloud_job_uuid,
                system_exception_code=system_exception_code,
                exit_code=self.compute_state.get('exit_code', None),
            )

        deregistered_due_to_error = False
        if self._job_worker_process:
            logger_no_user_data.debug(
                f'Job "{self._job_uuid}" terminating JobWorkerProcess with PID {self._job_worker_process.pid}'
            )
            self._job_worker_process.terminate()

            clean_up_timeout_in_seconds = 600
            for _ in range(clean_up_timeout_in_seconds):
                if self._job_worker_process.exitcode is not None:
                    logger_no_user_data.debug(
                        f'Job "{self._job_uuid}" worker process exitcode {self._job_worker_process.exitcode}'
                    )
                    break
                else:
                    logger_no_user_data.debug(f'Job "{self._job_uuid}" waiting for worker process to exit...')
                    time.sleep(1)

            if self._job_worker_process.exitcode is None:
                # TODO: Figure out if more error handling is necessary here
                logger_no_user_data.error(
                    f'Job {self._job_uuid} worker process did not exit within {clean_up_timeout_in_seconds} seconds'
                )
                if utils.IS_RUNNING_IN_CLOUD:
                    logger_no_user_data.error('Deregistering compute node...')
                    CloudUtils.deregister(error='job_cleanup_timed_out')
                    deregistered_due_to_error = True

            elif system_exception_code in [
                SystemExceptionCodes.CANCELLED_BY_USER.value,
                SystemExceptionCodes.EXCEEDED_MAX_JOB_RUNTIME.value,
            ]:
                self.compute_state['exit_code'] = self._upload_module_output_and_get_exit_code()
                CloudUtils.finish_cloud_job(
                    cloud_job_id=cloud_job_uuid,
                    system_exception_code=system_exception_code,
                    exit_code=self.compute_state.get('exit_code', None),
                )

        # Delete result as error occurred
        if system_exception_code and os.path.exists(self._job_temporary_dir):
            shutil.rmtree(self._job_temporary_dir)

        if self._socket:
            self._socket.close()

        if self._connection:
            self._connection.close()

        if self.compute_state['progress'] == 95:
            seconds_to_sleep = 5
            logger_no_user_data.debug(
                f'Job "{self._job_uuid}" worker thread sleeping for {seconds_to_sleep} seconds before cleaning up'
            )
            # sleep to let the user start downloading the result
            time.sleep(seconds_to_sleep)

        compute_state_dict = webserver_utils.JOB_ID_TO_COMPUTE_STATE_DICT
        if self._job_uuid in compute_state_dict:
            # Delete result as user has not started download
            if compute_state_dict[self._job_uuid]['progress'] == 95 and os.path.exists(self._job_temporary_dir):
                shutil.rmtree(self._job_temporary_dir)

            webserver_utils.JOB_ID_TO_COMPUTE_STATE_DICT.pop(self._job_uuid)
            logger_no_user_data.debug(f'Job "{self._job_uuid}" was cleaned up')
        else:
            logger_no_user_data.debug(
                f'Job "{self._job_uuid}" could not be found, maybe it has already been cleaned up'
            )

        if utils.IS_RUNNING_IN_CLOUD:
            config = CloudUtils.get_webserver_config()
            logger_no_user_data.debug(f'Job "{self._job_uuid}" reporting CloudJob "{cloud_job_uuid}" as cleaned up...')
            api.client.post(
                path=f'/internal/compute-nodes/cloud-jobs/{cloud_job_uuid}/cleaned-up/',
                headers={'Compute-Node-Auth-Token': config['compute_node_info']['auth_token']},
            )

            if deregistered_due_to_error:
                CloudUtils.shutdown()  # shutdown now
            else:
                webserver_utils.update_auto_shutdown_time()

        logger_no_user_data.debug(f'Job "{self._job_uuid}" worker thread exiting...')
        sys.exit()
