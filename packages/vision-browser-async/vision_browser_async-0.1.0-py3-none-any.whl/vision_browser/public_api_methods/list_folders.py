from ..base import BaseAPIMethod
from ..models import Folder


class ListFolders(BaseAPIMethod):
    async def _execute_impl(self) -> list[Folder]:
        data = await self.session.get(self.public_api_endpoint + "/folders")
        return Folder.load_list(data["data"])