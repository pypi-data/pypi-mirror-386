from typing import Literal

from ..base import BaseAPIMethod
from ..models import Fingerprint


class GetFingerprint(BaseAPIMethod):
    async def _execute_impl(
            self,
            platform: Literal["macos", "windows", "linux"],
            version: int | None = None
    ) -> Fingerprint:
        data = await self.session.get(self.public_api_endpoint + f"/fingerprints/{platform}/{version or 'latest'}")
        return Fingerprint.load(data["data"]["fingerprint"])
