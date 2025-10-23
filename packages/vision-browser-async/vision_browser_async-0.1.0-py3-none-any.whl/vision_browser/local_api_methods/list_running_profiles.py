from ..base import BaseAPIMethod
from ..models import RunningProfile


class ListRunningProfiles(BaseAPIMethod):
    async def _execute_impl(self) -> list[RunningProfile]:
        data = await self.session.get(self.local_api_endpoint + "/list")
        return RunningProfile.load_list(data["profiles"])