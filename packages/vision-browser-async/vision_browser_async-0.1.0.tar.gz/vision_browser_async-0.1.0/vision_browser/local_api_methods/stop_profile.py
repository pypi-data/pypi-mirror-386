import asyncio

from ..base import BaseAPIMethod
from ..models import Profile, RunningProfile


class StopProfile(BaseAPIMethod):
    async def _execute_impl(self, profile: Profile | RunningProfile, wait_until_close: bool | None = None) -> None:
        profile_id = profile.id if isinstance(profile, Profile) else profile.profile_id
        endpoint = self.local_api_endpoint + f"/stop/{profile.folder_id}/{profile_id}"
        await self.session.get(endpoint)
        if wait_until_close:
            for i in range(5):
                running_profiles = await self.vision_api.list_running_profiles()
                for running_profile in running_profiles:
                    if running_profile.profile_id == profile_id and running_profile.folder_id == profile.folder_id:
                        break
                else:
                    return
                await asyncio.sleep(2)
            raise TimeoutError
        await asyncio.sleep(2)
