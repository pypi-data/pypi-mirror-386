import json
import ssl
import time
import uuid
from typing import Optional

import websockets


class WebsocketConnectException(Exception):
    """Ошибка подлючения к вебсокету."""

    def __init__(self, message='Ошибка подлючения к вебсокету'):
        self.message = message
        super().__init__(self.message)


class WebsocketClient:
    """Клиент websocket для чат клиента."""

    def __init__(
            self,
            websocket_url: str,
            username: str,
            session,
    ):
        """
        Инициализация websocket клиента.

        :param websocket_url: url для подключения по websocket
        :param username: Имя пользователя для которого создается клиент

        :returns: None
        """
        self._websocket_url: str = websocket_url

        self.websocket_client: websockets.ClientConnection = None
        self.username: str = username
        self.connected: bool = False
        self.user_token = session.headers['X-Auth-Token']
        self.user_uid = session.headers['X-User-Id']

    async def init_websocket(self) -> None:
        """
        Создание клиента websocket для юзера.

        :returns: None
        """
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ws_client = await websockets.connect(self._websocket_url,
                                             ssl=ssl_context,
                                             ping_interval=4,
                                             ping_timeout=10,
                                             )
        await ws_client.send(json.dumps(
            {
                'msg': 'connect',
                'version': '1',
                'support': ['1'],
            },
        ),
        )
        connection_result = await ws_client.recv()
        result = json.loads(connection_result)
        connection_status = result['msg']
        connection_session = result['session']
        await self.login(ws_client=ws_client)
        if connection_status == 'connected' and connection_session is not None:
            self.websocket_client = ws_client
        else:
            raise WebsocketConnectException

    async def login(self, ws_client: websockets.ClientConnection) -> None:
        """
        Авторизация по websocket.

        :return: tuple[str, dict]
        """
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'login',
            'msg': 'method',
            'params': [
                {
                    'resume': self.user_token,
                },
            ],
        }
        json_data = json.dumps(data)
        await ws_client.send(json_data)
        await ws_client.recv()
        try:
            login_result = await ws_client.recv()
            login_data = json.loads(login_result)
            login_result = login_data.get('result')
            login_result.get('token')
            self.connected = True
        except (KeyError, AttributeError):
            raise WebsocketConnectException(
                message=f'error: {login_data["error"]["reason"]}',
            )

    async def load_message_history(
            self,
            room_id: str,
            message_limit: int = 50,
    ) -> tuple[str, dict]:
        """....
        Загрузка N сообщений в комнате/лс и тд.

        :param room_id: id комнаты из которого грузить сообщения
        :param message_limit: лимит сообщений

        :return: tuple[str, dict]
        """
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'v2/loadHistory',
            'msg': 'method',
            'params': [
                {
                    'rid': room_id,
                    'limit': message_limit,
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return request_id, data

    async def get_room_roles(
            self,
            room_id: str,
    ) -> tuple[str, dict]:
        """
        Получение ролей участников в комнате.

        :param room_id: id комнаты

        :return: tuple[str, dict]
        """
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'getRoomRoles',
            'msg': 'method',
            'params': [room_id],
        }
        await self.websocket_client.send(json.dumps(data))
        return request_id, data

    async def update_message(
            self,
            room_id: str,
            message_id: str,
            message_text: str,
            markdown: Optional[dict] = None,
            pings: Optional[list[str]] = [],
            urls: Optional[list[str]] = [],
    ) -> tuple[str, dict]:
        """Изменение сообщения.

        :param room_id: id комнаты

        :return: tuple[str, dict]
        """
        if markdown:
            md_data = markdown
        else:
            md_data = {
                'type': 'PLAIN_TEXT',
                'value': message_text,
            }
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'updateMessage',
            'msg': 'method',
            'params': [
                {
                    'editedAt': time.time(),
                    'editedBy': {
                        'username': self.username,
                        '_id': self.user_uid,
                    },
                    'md': md_data,
                    'mentions': pings,
                    'msg': message_text,
                    'rid': room_id,
                    'ts': {
                        '$data': time.time(),
                    },
                    'u': {
                        'username': self.username,
                        '_id': self.user_uid,
                        'name': '',
                    },
                    'urls': urls,
                    '_id': message_id,
                    '_updatedAt': time.time(),
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return request_id, data

    async def delete_messages(
            self,
            room_id: str,
            messages_id: list[str],
    ) -> tuple[str, dict]:
        """
        Удаление N сообщений в комнате.

        :param room_id: id комнаты
        :param messages_id: список id сообщений для удаления

        :return: tuple[str, dict]
        """
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'deleteMessages',
            'msg': 'method',
            'params': [
                messages_id,
                room_id,
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return request_id, data

    async def read_message_before(
            self,
            room_id: list[str],
            read_date: float,
    ) -> tuple[str, dict]:
        """
        Прочтение сообщений в комнате до определенной даты.

        :param room_id: id комнаты
        :param read_date: timestamp до какого даты ставить отметку

        :return: tuple[str, dict]
        """
        request_id = str(uuid.uuid4())
        data = {
            'id': request_id,
            'method': 'readMessagesBefore',
            'msg': 'method',
            'params': [room_id, {'$date': read_date}],
        }
        await self.websocket_client.send(json.dumps(data))
        return request_id, data

    async def subscribe_room_changed(self) -> str:
        """Подписка на изменения комнат.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/rooms-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_readmark_changed(self) -> str:
        """Подписка которая присылает информацию что сообщение до даты.
        кто-то прочитал

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/readmark-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_preferences_changed(self) -> str:
        """Подписка на изменение настроек по методу /api/v1/preferences.set.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/preferences-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_subscriptions_changed(self) -> str:
        """Подписка на изменения персональной информации о комнате.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/subscriptions-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_notification(self) -> str:
        """Подписка на получение новых сообщений.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/notification',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_messages_changed(self) -> str:
        """Подписка на изменения сообщений.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/messages-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def subscribe_folders_changed(self) -> str:
        """Подписка на изменения папок.

        :param user_id: uid пользователя

        :return: str (uid запроса)
        """
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.user_uid}/folders-changed',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        await self.websocket_client.send(json.dumps(data))
        return uid

    async def logout(self) -> None:
        """
        Выход из аккаунта по websocket.

        :return: dict[str, str, str, list] | None
        """
        data = {
            'id': str(uuid.uuid4()),
            'method': 'logout',
            'msg': 'method',
            'params': [],
        }
        await self.websocket_client.send(json.dumps(data))
        return None

    async def close_websocket(self) -> None:
        """Закрывает соединение по вебсокету."""
        await self.websocket_client.close()
