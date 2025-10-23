from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Folder, Proxy
from ..utils.proxy import proxy_to_payload
from ..utils.validators import extract_folder_id


class CreateProxies(BaseAPIMethod):
    async def _execute_impl(self, folder_id: Folder | UUID | str, proxies: list[str]) -> list[Proxy]:
        folder_id = extract_folder_id(folder_id)

        payload = {"proxies": [proxy_to_payload(p) for p in proxies]}
        data = await self.session.post(self.public_api_endpoint + f"/folders/{folder_id}/proxies", json=payload)

        container = data.get("data") if isinstance(data, dict) and "data" in data else data
        items = container or []
        return Proxy.load_list(items)
