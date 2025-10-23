from .utils import MyAsyncClient, MyClient
from typing import Protocol


class Init(Protocol):
    _logged: bool = False
    _SID: str
    _login: str
    _password: str


class AsyncASURSO(Init):
    _client: MyAsyncClient


class ASURSO(Init):
    _client: MyClient


__all__ = ["AsyncASURSO", "ASURSO"]
