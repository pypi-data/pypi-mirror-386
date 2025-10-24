# ECSS Chat Client

Python клиент для работы с ECSS Chat.

## Install

```bash
pip install ecss-chat-client
```

## GetStarted

```python
from ecss_chat_client import Client
```


## Basic HTTP Client

### Basic user
```python
client=Client(
    server=Params.SERVER_IP,
    proto=Params.PROTOCOL,
    port=Params.SERVER_PORT,
    verify=False,
)
client.create_session(
    username=USERNAME, password=PASSWORD,
)
```

### Basic bot
```python
client=Client(
    server=Params.SERVER_IP,
    proto=Params.PROTOCOL,
    port=Params.SERVER_PORT,
    verify=False,
)
client.create_bot_session(token='You bot token')
```

## Simple Echo Bot

```python
class SimpleBot(Client):

    @decorator_service.ws_ping_wrapper(logger=logger)
    def on_message(self, ws: WebSocketApp, message):
        logger.info('### message ###')

        try:
            data = json.loads(message)
            received_message = data.get('msg')

            if received_message == 'connected':
                self.basic_websocket.auth()
            if received_message == 'result' and data.get('result').get('id'):
                self.basic_websocket.subscribe_notification()
            if received_message == 'changed':
                payload = data['fields']['args'][0]['payload']
                payload_type = payload['type']
                if payload_type == RoomTypes.DIRECT:
                    if len(payload['message']['msg']) > 0:
                        message = payload['message']['msg']
                        room_id = payload['rid']
                        self.messages.send(
                            text=message,
                            room_id=room_id,
                        )
        except json.JSONDecodeError:
            pass

    @staticmethod
    def on_error(ws: WebSocketApp, error):
        logger.error(error)

    @staticmethod
    def on_close(ws: WebSocketApp, close_status_code, close_msg):
        logger.warning('### closed ###')

    @staticmethod
    def send_message(client: Client, text, rid):
        client.messages.send(text, room_id=rid)


if __name__ == '__main__':
    bot_client = SimpleBot(server=SERVER, port=PORT, verify=False)
    bot_client.create_bot_session(token=TOKEN)
    logger.add('bot.log', rotation='500 MB')
    bot_client.basic_websocket.init_ws_client(
        on_message_handler=bot_client.on_message,
        on_error_handler=bot_client.on_error,
        on_close_handler=bot_client.on_close,
        token=TOKEN,
        client_uid=UID,
        logger=logger,
        websocket_trace=True,
    )
```
Вы можете обработать событие "on_pong" с помощью декоратора
```python
@decorator_service.ws_ping_wrapper(logger=logger)
def on_message(self, ws: WebSocketApp, message):
    logger.info('### message ###')

    try:
        data = json.loads(message)
        received_message = data.get('msg')
```

Вы можете обработать событие "on_pong" с помощью функции "ping_handler"
```python
def on_message(self, ws: WebSocketApp, message):
    logger.info('### message ###')

    try:
        data = json.loads(message)
        received_message = data.get('msg')

        if received_message == 'ping':
            self.basic_websocket.ping_handler()
```
Можно не передавать логер в декоратор с учетом, что кастомный логгер не был
добавлен в "init_ws_client"
```python
@decorator_service.ws_ping_wrapper()
def on_message(self, ws: WebSocketApp, message):
    logger.info('### message ###')

    try:
        data = json.loads(message)
        received_message = data.get('msg')
```