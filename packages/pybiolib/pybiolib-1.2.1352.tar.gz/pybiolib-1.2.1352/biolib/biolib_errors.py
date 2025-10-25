from typing import Optional


class BioLibError(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ValidationError(BioLibError):
    def __init__(self, message: Optional[str] = None):
        super().__init__(message=message or 'Invalid input.')

class NotFound(BioLibError):

    def __init__(self, message: Optional[str] = None):
        super().__init__(message=message or 'Not found.')


class DockerContainerNotFoundDuringExecutionException(Exception):
    pass


class RetryLimitException(Exception):
    pass


class StorageDownloadFailed(Exception):
    pass


class CloudJobFinishedError(Exception):
    pass


class JobResultError(BioLibError):
    pass


class JobResultNotFound(JobResultError):
    pass


class JobResultPermissionError(JobResultError):
    pass


class JobResultNonZeroExitCodeError(JobResultError):
    """Raised when an app returns a non-zero exit code and check=True."""
    def __init__(self, exit_code: int, message: Optional[str] = None):
        self.exit_code = exit_code
        super().__init__(
            message or f'App returned non-zero exit code: {exit_code}'
        )
