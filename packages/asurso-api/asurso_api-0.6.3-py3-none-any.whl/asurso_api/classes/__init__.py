from ..functions.attestation import Attestation
from ..functions.chats import Chat
from ..functions.dashboard import Dashboard
from ..functions.login import LoginInfo, LoginInfoPerm, LoginInfoTemp
from ..functions.info import Info
from ..functions.lessons import LessonsDay, Lesson
from ..functions.organization import Organization
from ..functions.reports import GroupAttestation, CurrentPerformance
from ..functions import (
    attestation,
    chats,
    dashboard,
    login,
    info,
    lessons,
    organization,
    reports,
)


from ..utils import MyAsyncClient, MyClient, hash_password
from ..functions import Methods, AsyncMethods
from typing import Union
import httpx
import logging


def handle_exc(exc):
    if exc and any(exc):
        builded_exc = exc[1]
        builded_exc.with_traceback(exc[2])
        raise builded_exc


class ASURSO(Methods):
    _SID: str
    _client: "MyClient"

    def __init__(
        self,
        login: str,
        password: str,
        timeout: int = 60,
        proxy: Union[httpx.URL, str, httpx.Proxy, None] = None,
        password_is_hashed: bool = False,
    ):
        """Args:
        login (Optional[str], optional): your ASURSO account's login. Defaults to None.
        password (Optional[str], optional): your ASURSO account's password. Defaults to None.
        cookie (Optional[str], optional): your ASURSO account's cookie. Defaults to None.
        timeout (int): httpx.AsyncClient's timeout in seconds. Defaults to 60.
        proxy (Union[httpx.Proxy, None], optional): proxy for httpx.AsyncClient. Defaults to None.
        password_is_hashed (bool): password is needed to be hashed or not. Defaults to False.
        """
        self._login = login
        self._password = password if password_is_hashed else hash_password(password)

        self._SID = ""
        self._client = MyClient(
            base_url="https://spo.asurso.ru", timeout=timeout, proxy=proxy
        )

    def __enter__(self):
        self.login(True)
        return self

    def __exit__(self, *exc):
        self.logout()
        handle_exc(exc)


class AsyncASURSO(AsyncMethods):
    _SID: str
    _client: "MyAsyncClient"

    def __init__(
        self,
        login: str,
        password: str,
        timeout: int = 60,
        proxy: Union[httpx.URL, str, httpx.Proxy, None] = None,
        password_is_hashed: bool = False,
    ):
        """Args:
        login (Optional[str], optional): your ASURSO account's login. Defaults to None.
        password (Optional[str], optional): your ASURSO account's password. Defaults to None.
        cookie (Optional[str], optional): your ASURSO account's cookie. Defaults to None.
        timeout (int): httpx.AsyncClient's timeout in seconds. Defaults to 60.
        proxy (Union[httpx.Proxy, None], optional): proxy for httpx.AsyncClient. Defaults to None.
        password_is_hashed (bool): password is needed to be hashed or not. Defaults to False.
        """
        self._login = login
        self._password = password if password_is_hashed else hash_password(password)

        self._SID = ""
        self._client = MyAsyncClient(
            base_url="https://spo.asurso.ru", timeout=timeout, proxy=proxy
        )

    async def __aenter__(self):
        await self.login(True)
        return self

    async def __aexit__(self, *exc):
        await self.logout()
        handle_exc(exc)


logger = logging.getLogger()


__all__ = [
    "attestation",
    "chats",
    "dashboard",
    "login",
    "info",
    "lessons",
    "organization",
    "reports",
    "Attestation",
    "Chat",
    "Dashboard",
    "LoginInfo",
    "LoginInfoPerm",
    "LoginInfoTemp",
    "Info",
    "LessonsDay",
    "Lesson",
    "Organization",
    "GroupAttestation",
    "CurrentPerformance",
    "Info",
    "ASURSO",
    "AsyncASURSO",
]
