import asyncio

import httpx

from ..base import BaseAPIMethod
from ..errors import VisionBrowserAPIError
from ..models import Profile, RunningProfile


class StartProfile(BaseAPIMethod):
    async def _wait_until_started(self, profile: Profile) -> RunningProfile:
        for i in range(30):
            running_profiles = await self.vision_api.list_running_profiles()
            for running_profile in running_profiles:
                if all((
                        running_profile.profile_id == profile.id,
                        running_profile.folder_id == profile.folder_id,
                        running_profile.port is not None
                )):
                    return running_profile
            await asyncio.sleep(5)
        raise TimeoutError

    async def _execute_impl(self, profile: Profile, args: list[str] | None = None,
                            wait_until_started: bool | None = None) -> RunningProfile:
        endpoint = self.local_api_endpoint + f"/start/{profile.folder_id}/{profile.id}"
        try:
            data = await self.session.post(endpoint, json={"args": args}) if args else await self.session.get(endpoint)
            return await self._wait_until_started(profile) if wait_until_started else RunningProfile.load(data)
        except VisionBrowserAPIError as e:
            if "Profile is already starting" in str(e):
                return await self._wait_until_started(profile)
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # raise ProfileAlreadyStartingError("Received 429 status error. "
                #                                   "It means that profile is already starting") from e
                return await self._wait_until_started(profile)
            raise
