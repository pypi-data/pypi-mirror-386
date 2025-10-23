from ..base import BaseAPIMethod
from ..models import Folder
from ..types import FolderColor, FolderIcon


class CreateFolder(BaseAPIMethod):
    async def _execute_impl(
            self,
            folder_name: str,
            folder_icon: FolderIcon | str | None = None,
            folder_color: FolderColor | str | None = None,
    ) -> Folder:
        body = {
            "folder_name": folder_name,
            "folder_icon": folder_icon or FolderIcon.__args__[0],
            "folder_color": folder_color or FolderColor.__args__[0],
        }

        payload = await self.session.post(self.public_api_endpoint + "/folders", json=body)

        container = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
        if isinstance(container, list):
            if not container:
                raise ValueError("Empty data list returned for CreateFolder")
            item = container[0]
        elif isinstance(container, dict):
            item = container
        else:
            raise ValueError("Unexpected CreateFolder response format")

        return Folder.load(item)
