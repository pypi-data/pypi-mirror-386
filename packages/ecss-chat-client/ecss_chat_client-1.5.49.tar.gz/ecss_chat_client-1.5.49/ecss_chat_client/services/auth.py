from http import HTTPStatus

import requests

from ..scheme import AuthResponse


class AuthenticationError(Exception):
    """Исключение для ошибок аутентификации."""


def auth(
        username: str,
        password: str,
        server: str,
        proto: str,
        port: str,
        verify: bool,
) -> tuple[str, str]:
    url = f'{proto}://{server}:{port}/api/v1/login'
    login_data = {
        'user': username,
        'password': password,
    }
    if proto == 'http':
        response = requests.post(
            url,
            json=login_data,
        )
    else:
        response = requests.post(
            url,
            json=login_data,
            verify=verify,
        )
    if response.status_code != HTTPStatus.OK:
        raise AuthenticationError('Maybe?- SYSTEM_ADMIN_PASSWORD=password')
    auth_response = AuthResponse(**response.json())
    token = auth_response.data.authToken
    uid = auth_response.data.me.id
    return token, uid
