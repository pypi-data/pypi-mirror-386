import base64
import binascii
import json
from datetime import datetime, timezone
from json.decoder import JSONDecodeError
from urllib.parse import urlencode, urljoin

import importlib_metadata

from biolib._internal.http_client import HttpClient, HttpResponse
from biolib._internal.types.typing import Any, Dict, Optional, TypedDict, Union, cast
from biolib.biolib_api_client import BiolibApiClient as DeprecatedApiClient
from biolib.biolib_errors import BioLibError
from biolib.biolib_logging import logger

OptionalHeaders = Union[
    Optional[Dict[str, str]],
    Optional[Dict[str, Union[str, None]]],
]


def _get_biolib_package_version() -> str:
    # try fetching version, if it fails (usually when in dev), add default
    try:
        return cast(str, importlib_metadata.version('pybiolib'))
    except importlib_metadata.PackageNotFoundError:
        return '0.0.0'


class ApiClientInitDict(TypedDict):
    refresh_token: str
    base_url: str
    client_type: Optional[str]


class JwtDecodeError(Exception):
    pass


class ApiClient(HttpClient):
    _biolib_package_version: str = _get_biolib_package_version()

    def __init__(self, _init_dict: Optional[ApiClientInitDict] = None) -> None:
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = _init_dict['refresh_token'] if _init_dict else None
        self._base_url: Optional[str] = _init_dict['base_url'] if _init_dict else None
        self._client_type: Optional[str] = _init_dict['client_type'] if _init_dict else None

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Union[str, int]]] = None,
        headers: OptionalHeaders = None,
        authenticate: bool = True,
        retries: int = 10,
    ) -> HttpResponse:
        return self.request(
            headers=self._get_headers(opt_headers=headers, authenticate=authenticate),
            method='GET',
            retries=retries,
            url=self._get_absolute_url(path=path, query_params=params),
        )

    def post(
        self,
        path: str,
        data: Optional[Union[Dict, bytes]] = None,
        headers: OptionalHeaders = None,
        authenticate: bool = True,
        retries: int = 50,  # TODO: reduce this back to 5 when timeout errors have been solved
    ) -> HttpResponse:
        return self.request(
            data=data,
            headers=self._get_headers(opt_headers=headers, authenticate=authenticate),
            method='POST',
            retries=retries,
            url=self._get_absolute_url(path=path, query_params=None),
        )

    def patch(
        self,
        path: str,
        data: Dict,
        headers: OptionalHeaders = None,
        retries: int = 5,
        params: Optional[Dict[str, Union[str, int]]] = None,
    ) -> HttpResponse:
        return self.request(
            data=data,
            headers=self._get_headers(opt_headers=headers, authenticate=True),
            method='PATCH',
            retries=retries,
            url=self._get_absolute_url(path=path, query_params=params),
        )

    def delete(
        self,
        path: str,
        headers: OptionalHeaders = None,
        retries: int = 0,
    ) -> HttpResponse:
        return self.request(
            headers=self._get_headers(opt_headers=headers, authenticate=True),
            method='DELETE',
            retries=retries,
            url=self._get_absolute_url(path=path, query_params=None),
        )

    def _get_headers(self, opt_headers: OptionalHeaders, authenticate: bool) -> Dict[str, str]:
        # Only keep header keys with a value
        headers: Dict[str, str] = {key: value for key, value in (opt_headers or {}).items() if value}

        if authenticate:
            if self._refresh_token:
                headers['Authorization'] = f'Bearer {self._get_access_token()}'
            else:
                # TODO: Remove this block when deprecated api client is removed
                deprecated_api_client = DeprecatedApiClient.get()
                if deprecated_api_client.is_signed_in:
                    deprecated_api_client.refresh_access_token()

                if deprecated_api_client.resource_deploy_key:
                    headers['Authorization'] = f'Token {deprecated_api_client.resource_deploy_key}'
                else:
                    # Adding access_token outside is_signed_in check as job_worker.py currently sets access_token
                    # without setting refresh_token
                    access_token = deprecated_api_client.access_token
                    if access_token:
                        headers['Authorization'] = f'Bearer {access_token}'

        headers['client-type'] = 'biolib-python'
        headers['client-version'] = ApiClient._biolib_package_version
        if self._client_type:
            headers['client-opt-type'] = self._client_type

        return headers

    def _get_absolute_url(self, path: str, query_params: Optional[Dict[str, Union[str, int]]]) -> str:
        deprecated_api_client = DeprecatedApiClient.get()
        base_url = self._base_url or deprecated_api_client.base_url
        base_api_url = urljoin(base_url, '/api/')
        url = urljoin(base_api_url, path.strip('/') + '/')
        if query_params:
            url = url + '?' + urlencode(query_params)

        return url

    def _get_access_token(self) -> str:
        if self._access_token:
            decoded_token = self._decode_jwt_without_checking_signature(self._access_token)
            if datetime.now(tz=timezone.utc).timestamp() < decoded_token['payload']['exp'] - 60:  # 60 second buffer
                # Token has not expired yet
                return self._access_token

        # TODO: Implement nicer error handling
        try:
            response = HttpClient.request(
                method='POST',
                url=f'{self._base_url}/api/user/token/refresh/',
                data={'refresh': self._refresh_token},
            )
        except Exception as exception:
            logger.error('Sign in with refresh token failed')
            raise exception

        try:
            response_dict = response.json()
        except JSONDecodeError as error:
            logger.error('Could not decode response from server as JSON:')
            raise BioLibError(response.text) from error

        self._access_token = cast(str, response_dict['access'])
        return self._access_token

    @staticmethod
    def _decode_jwt_without_checking_signature(jwt: str) -> Dict[str, Any]:
        jwt_bytes = jwt.encode('utf-8')

        try:
            signing_input, _ = jwt_bytes.rsplit(b'.', 1)
            header_segment, payload_segment = signing_input.split(b'.', 1)
        except ValueError as error:
            raise JwtDecodeError('Not enough segments') from error

        try:
            header_data = base64.urlsafe_b64decode(header_segment)
        except (TypeError, binascii.Error) as error:
            raise JwtDecodeError('Invalid header padding') from error

        try:
            header = json.loads(header_data)
        except ValueError as error:
            raise JwtDecodeError(f'Invalid header string: {error}') from error

        if not isinstance(header, dict):
            raise JwtDecodeError('Invalid header string: must be a json object')

        try:
            payload_data = base64.urlsafe_b64decode(payload_segment)
        except (TypeError, binascii.Error) as error:
            raise JwtDecodeError('Invalid payload padding') from error

        try:
            payload = json.loads(payload_data)
        except ValueError as error:
            raise JwtDecodeError(f'Invalid payload string: {error}') from error

        if not isinstance(header, dict):
            raise JwtDecodeError('Invalid payload string: must be a json object')

        return dict(header=header, payload=payload)
