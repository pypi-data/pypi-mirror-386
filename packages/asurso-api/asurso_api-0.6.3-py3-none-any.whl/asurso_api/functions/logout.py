from ..utils import MyAsyncClient, MyClient
from ..typing import AsyncASURSO, ASURSO
from typing import Union
from httpx import Response
import logging


logger = logging.getLogger(__name__)


def _parse(client: Union[MyAsyncClient, MyClient], r: Response):
    client.headers.clear()
    client.cookies.clear()
    # client.cookies.update(r.cookies)

    if r.status_code != 200:
        logger.error(f"{r=}, {r.text=}, {r.status_code=}")

    return r.status_code == 200


async def logout_async(client: MyAsyncClient) -> bool:
    r = await client.delete("/services/security/logout")
    return _parse(client, r)


def logout_sync(client: MyClient) -> bool:
    r = client.delete("/services/security/logout")
    return _parse(client, r)


class AsyncLogoutMethod(AsyncASURSO):
    async def logout(self: AsyncASURSO):
        r = await logout_async(self._client)
        self._logged = False
        return r


class LogoutMethod(ASURSO):
    def logout(self: ASURSO):
        r = logout_sync(self._client)
        self._logged = False
        return r
