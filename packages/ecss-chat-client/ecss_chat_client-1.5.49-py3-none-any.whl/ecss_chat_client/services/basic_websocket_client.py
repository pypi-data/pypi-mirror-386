import json
import logging
import ssl
import uuid
from typing import Any, Optional

import rel
import websocket
from websocket import WebSocketApp


class BasicWebsocketClient:
    """Websocket клиент для установки длительных соединений."""

    def __init__(
            self,
            websocket_url: str,
    ) -> None:
        self.websocket_client: WebSocketApp = None # noqa
        self.websocket_url: str = websocket_url
        self.token: str | None = None
        self.client_uid: str | None = None
        self.logger: Any = None

    def init_ws_client(
            self,
            on_message_handler: callable,
            on_error_handler: callable,
            on_close_handler: callable,
            token: str,
            client_uid: str,
            logger: Optional[Any] = None,
            on_ping_handler: Optional[callable] = None,
            websocket_trace: Optional[bool] = False,
    ) -> None:
        """Инициализация базового Ws клиента.

        :param on_message_handler: Хэндлер входящих сообщений
        :param on_error_handler:  Хэндлер ошибок
        :param on_close_handler: Хэндлер закрытия соединения
        :param token: Токен
        :param client_uid: UDI Клиента
        :param logger: Логер(например Loguru)
        :param on_ping_handler: Хэндлер пингов
        :param websocket_trace: Трасировка вебсокета

        :return: None
        """
        websocket.enableTrace(websocket_trace)
        self.token = token
        self.client_uid = client_uid
        if on_ping_handler is None:
            on_ping_handler = on_message_handler
        if logger:
            self.logger = logger
        if not logger:
            logger = logging.getLogger(__name__)
            self.logger = logger
            logging.basicConfig(filename='base_bot.log', level=logging.INFO)
            logger.info('### START LOGGING ###')
        self.websocket_client = websocket.WebSocketApp(
            url=self.websocket_url,
            on_open=self.open_connection,
            on_message=on_message_handler,
            on_error=on_error_handler,
            on_close=on_close_handler,
            on_ping=on_ping_handler,
        )
        self.websocket_client.run_forever(
            dispatcher=rel,
            reconnect=5,
            sslopt={
                'cert_reqs': ssl.CERT_NONE,
                'check_hostname': False,
            },
        )
        rel.signal(sig=2, callback=rel.abort)
        rel.dispatch()

    def open_connection(self, ws_client: WebSocketApp) -> None:
        """Открытие соединения с WS elph chat.

        :param ws_client: Экземпляр ws клиента

        :return: None
        """
        self.logger.info('### Open connection ###')
        connect_data = {
            'msg': 'connect',
            'version': '1',
            'support': ['1'],
        }
        ws_client.send(json.dumps(connect_data))

    def ping_handler(self) -> None:
        """Хэндлер пингов.

        :return: None
        """
        self.logger.info('### PING ###')
        pong_data = {'msg': 'pong'}
        self.websocket_client.send(json.dumps(pong_data))

    def auth(self) -> None:
        """Авторизация по WS в Elph Chat.

        :return: None
        """
        self.logger.info('### WS Authorization ###')
        auth_uid = str(uuid.uuid4())
        auth_data = {
            'msg': 'method',
            'method': 'login',
            'params': [
                {'resume': self.token},
            ],
            'id': auth_uid,
        }
        self.websocket_client.send(json.dumps(auth_data))

    def subscribe_notification(self) -> None:
        """Подписка на уведомления.

        :return: None
        """
        self.logger.info('### Message subscription ###')
        uid = str(uuid.uuid4())
        data = {
            'msg': 'sub',
            'id': uid,
            'name': 'stream-notify-user',
            'params': [
                f'{self.client_uid}/notification',
                {
                    'useCollection': False,
                    'args': [],
                },
            ],
        }
        self.websocket_client.send(json.dumps(data))
