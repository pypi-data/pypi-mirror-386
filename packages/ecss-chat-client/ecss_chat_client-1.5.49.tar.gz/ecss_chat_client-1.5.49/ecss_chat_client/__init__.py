"""ECSS Chat Client - Python клиент для ECSS Chat."""
import requests
from requests import Session

from .services.auth import auth
from .services.avatar import Avatars
from .services.basic_websocket_client import BasicWebsocketClient
from .services.bots import Bots
from .services.config import Settings
from .services.directs import Directs
from .services.folders import Folders
from .services.groups import Groups
from .services.info import ApiInfo
from .services.messages import Messages
from .services.polls import Polls
from .services.preferences import UserPreferences
from .services.rooms import Rooms
from .services.server import ServerSettings
from .services.spotlight import Spotlight
from .services.supergroups import SuperGroups
from .services.test_websocket_client import TestWebsocketClient
from .services.testing import Testing
from .services.threads import Threads
from .services.tus import TusService
from .services.users import Users


class Client:
    def __init__(
            self,
            server,
            port='3443',
            proto='https',
            verify=True,
    ):
        self.port = port
        self.proto = proto
        self.verify = verify
        self.server = server
        self.base_url = f'{proto}://{server}:{port}/api/v1'
        self.short_url = f'{proto}://{server}:{port}/api'
        self.__websocket_url = f'wss://{server}:{port}/websocket'
        self.session: Session | None = None
        self.settings = Settings(
            server, config_file='settings.ini',
        )
        self.test_websocket = None
        self.basic_websocket = BasicWebsocketClient(
            websocket_url=self.__websocket_url,
        )
        self.avatars = Avatars(self)
        self.directs = Directs(self)
        self.groups = Groups(self)
        self.polls = Polls(self)
        self.rooms = Rooms(self)
        self.supergroups = SuperGroups(self)
        self.folders = Folders(self)
        self.users = Users(self)
        self.preferences = UserPreferences(self)
        self.messages = Messages(self)
        self.threads = Threads(self)
        self.testing = Testing(self)
        self.spotlight = Spotlight(self)
        self.tus = TusService(self)
        self.api_info = ApiInfo(self)
        self.server_settings = ServerSettings(self)
        self.bots = Bots(self)

    def create_session(
            self,
            username: str,
            password: str,
    ) -> None:
        auth_token, uid = auth(
            username=username,
            password=password,
            server=self.server,
            proto=self.proto,
            port=self.port,
            verify=self.verify,
        )
        session = requests.Session()
        headers = {
            'X-Auth-Token': auth_token,
            'X-User-Id': uid,
        }
        session.headers.update(headers)
        session.cookies.set('rc_token', auth_token)
        session.cookies.set('rc_uid', uid)
        session.username = username
        session.uid = uid
        self.session = session
        self.test_websocket = TestWebsocketClient(
            self.__websocket_url,
            username=username,
            session=session,
        )

    def create_bot_session(self, token: str) -> None:
        session = requests.Session()
        headers = {
            'X-Auth-Token': token,
        }
        session.headers.update(headers)
        self.session = session


__all__ = ['Client']
__version__ = '1.5.49'
__author__ = 'Eltex SC VoIP'
__description__ = 'ElphChat API Client Library'
