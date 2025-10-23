from ..utils import parse_response, MyAsyncClient, MyClient
from ..typing import AsyncASURSO, ASURSO
from typing import List
from pydantic import BaseModel
import logging


logger = logging.getLogger(__name__)


class Subject(BaseModel):
    mark: float
    name: str
    id: int


class Dashboard(BaseModel):
    subjects: List[Subject]


async def get_dashboard_async(client: MyAsyncClient) -> Dashboard:
    r = await client.get(f"services/students/{client._SID}/dashboard")
    return parse_response(r, Dashboard)


def get_dashboard_sync(client: MyClient) -> Dashboard:
    r = client.get(f"services/students/{client._SID}/dashboard")
    return parse_response(r, Dashboard)


class AsyncGetDashboardMethod(AsyncASURSO):
    async def get_dashboard(self: AsyncASURSO) -> Dashboard:
        return await get_dashboard_async(self._client)


class GetDashboardMethod(ASURSO):
    def get_dashboard(self: ASURSO) -> Dashboard:
        return get_dashboard_sync(self._client)
