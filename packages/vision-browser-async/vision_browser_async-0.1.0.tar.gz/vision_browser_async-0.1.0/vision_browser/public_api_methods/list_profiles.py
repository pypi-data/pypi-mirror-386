from __future__ import annotations

from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Profile, Folder
from ..utils.validators import extract_folder_id


class ListProfiles(BaseAPIMethod):
    async def _execute_impl(self, folder_id: Folder | UUID | str, name: str | None = None) -> list[Profile]:
        folder_id = extract_folder_id(folder_id)

        endpoint = self.public_api_endpoint + f"/folders/{folder_id}/profiles"
        page_size = 50
        pn = 0
        all_items: list[dict] = []

        while True:
            params = {
                "folderId": folder_id,
                "pn": pn,
                "ps": page_size,
            }
            if name is not None:
                params["name"] = name

            payload = await self.session.get(endpoint, params=params)

            container = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
            if isinstance(container, dict):
                items = container.get("items") or []
                total = container.get("total")
            else:
                items = container or []
                total = None

            if not items:
                break

            all_items.extend(items)

            if isinstance(total, int) and len(all_items) >= total:
                break
            if len(items) < page_size:
                break

            pn += 1

        return Profile.load_list(all_items)
