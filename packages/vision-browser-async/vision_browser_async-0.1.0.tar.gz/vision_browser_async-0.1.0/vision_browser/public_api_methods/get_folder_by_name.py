from ..base import BaseAPIMethod
from ..models import Folder


class GetFolderByName(BaseAPIMethod):
    async def _execute_impl(self, folder_name: str) -> Folder | None:
        folders = await self.vision_api.list_folders()
        for folder in folders:
            if folder.folder_name == folder_name and folder.deleted_at is None:
                return folder
        return None
