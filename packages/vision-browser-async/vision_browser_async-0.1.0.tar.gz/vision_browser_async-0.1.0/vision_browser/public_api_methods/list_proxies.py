from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Folder, Proxy
from ..utils.validators import extract_folder_id


class ListProxies(BaseAPIMethod):
    async def _execute_impl(self, folder_id: Folder | UUID | str) -> list[Proxy]:
        folder_id = extract_folder_id(folder_id)

        url = self.public_api_endpoint + f"/folders/{folder_id}/proxies"
        payload = await self.session.get(url)

        container = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
        items = container or []
        return Proxy.load_list(items)
