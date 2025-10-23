from ..utils import parse_response, MyAsyncClient, MyClient
from ..typing import AsyncASURSO, ASURSO
from .. import enums
from pydantic import BaseModel, Field
from typing import List
import logging


logger = logging.getLogger(__name__)


class Chat(BaseModel):
    num: int
    id: int
    name: str
    chat_type: enums.ChatType = Field(..., alias="chatType")
    count_of_members: int = Field(..., alias="countOfMembers")
    admin_name: str = Field(..., alias="adminName")


async def get_chats_async(client: MyAsyncClient) -> List[Chat]:
    r = await client.get("/integration/chatManagement/chats/current")
    return parse_response(r, [Chat])


def get_chats_sync(client: MyClient) -> List[Chat]:
    r = client.get("/integration/chatManagement/chats/current")
    return parse_response(r, [Chat])


class AsyncGetChatsMethod(AsyncASURSO):
    async def get_chats(self: AsyncASURSO) -> List[Chat]:
        return await get_chats_async(self._client)


class GetChatsMethod(ASURSO):
    def get_chats(self: ASURSO) -> List[Chat]:
        return get_chats_sync(self._client)
