from ..base import BaseAPIMethod
from ..models import Folder, Profile


class GetProfileByName(BaseAPIMethod):
    async def _find_profile_by_name(self, folder_id: str, profile_name: str) -> Profile | None:
        data = await self.session.get(self.public_api_endpoint + f"/folders/{folder_id}/profiles")
        for profile in data["data"]["items"]:
            if profile["profile_name"] == profile_name:
                return Profile.load(profile)
        return None

    async def _execute_impl(self, profile_name: str, folder_id: Folder | str | None = None) -> Profile | None:
        folder_id = folder_id.id if isinstance(folder_id, Folder) else folder_id
        if folder_id:
            return await self._find_profile_by_name(folder_id, profile_name)
        else:
            folders = await self.vision_api.list_folders()
            for folder in folders:
                if profile := await self._find_profile_by_name(folder.id, profile_name):
                    return profile
            return None
