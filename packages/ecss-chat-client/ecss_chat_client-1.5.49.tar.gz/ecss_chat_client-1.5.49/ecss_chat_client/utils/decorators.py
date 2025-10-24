import json
import logging
from typing import Any, Optional

from websocket import WebSocketApp


class DecoratorsService:

    @staticmethod
    def paginate(function: callable):
        """Установка пагинации."""

        def wrapper(self, *args, **kwargs):
            if 'count' not in kwargs:
                kwargs['count'] = self.settings.count
            if 'offset' not in kwargs:
                kwargs['offset'] = self.settings.offset
            return function(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def ws_ping_wrapper(logger: Optional[Any] = None):
        """Декоратор для Pong ответов по WS.

        :param logger: Кастомный логер(например Loguru)

        """
        if not logger:
            logger = logging.getLogger(__name__)

        def ping_wrapper(function: callable):
            def wrapper(self, *args, **kwargs):
                msg: dict = json.loads(args[1])
                ws_client: WebSocketApp = args[0]
                if msg.get('msg') == 'ping':
                    logger.info('### WRAPPER PING ###')
                    pong_data = {'msg': 'pong'}
                    ws_client.send(json.dumps(pong_data))
                return function(self, *args, **kwargs)

            return wrapper

        return ping_wrapper


decorator_service = DecoratorsService()
