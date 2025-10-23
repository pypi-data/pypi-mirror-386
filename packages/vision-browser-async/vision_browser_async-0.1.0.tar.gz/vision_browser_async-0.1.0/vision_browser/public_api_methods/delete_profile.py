from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Profile, RunningProfile, Folder
from ..utils.validators import resolve_folder_and_profile_ids


class DeleteProfile(BaseAPIMethod):
    async def _execute_impl(
            self,
            profile: Profile | RunningProfile | UUID | str,
            folder: Folder | UUID | str | None = None
    ) -> Profile | str | None:
        folder_id, profile_id = resolve_folder_and_profile_ids(profile, folder)

        data = await self.session.delete(self.public_api_endpoint + f"/folders/{folder_id}/profiles/{profile_id}")
        if isinstance(data["data"], str):
            return data["data"]
        elif data["data"].pop("usage")["profiles"] == 1:
            return Profile.load(data["data"])
        else:
            return None
