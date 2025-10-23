from typing import Literal
from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Folder, Profile, Fingerprint, Proxy
from ..utils.validators import extract_folder_id, extract_proxy_id


class CreateProfile(BaseAPIMethod):
    async def _execute_impl(
            self,
            folder_id: Folder | UUID | str,
            profile_name: str,
            profile_notes: str | None = None,
            profile_tags: list[str] | None = None,
            proxy_id: Proxy | UUID | str | None = None,
            profile_status: list[tuple[str, str] | None] = None,
            platform: Literal["Windows", "Mac", "Linux"] = None,
            browser: Literal["Chrome"] = None,
            fingerprint: Fingerprint | None = None,
            webrtc_pref: Literal["auto", "off"] | str | None = None,
            webgl_pref: Literal["real", "off"] | float | None = None,
            canvas_pref: Literal["real", "off"] | float | None = None,
            ports_protection: list[int] | None = None,
    ) -> Profile:
        folder_id, proxy_id = extract_folder_id(folder_id), extract_proxy_id(proxy_id)

        if isinstance(webrtc_pref, str):
            webrtc_pref = {"manual": webrtc_pref}
        if isinstance(webgl_pref, float):
            webgl_pref = {"noise": webgl_pref}
        if isinstance(canvas_pref, float):
            canvas_pref = {"noise": canvas_pref}

        fingerprint = fingerprint.model_dump(mode="json")
        fingerprint.update({
            "webrtc_pref": webrtc_pref or "auto",
            "webgl_pref": webgl_pref or "off",
            "canvas_pref": canvas_pref or "off",
            "ports_protection": ports_protection or [],
        })
        body = {
            "profile_name": profile_name,
            "profile_notes": profile_notes or "",
            "profile_tags": profile_tags or [],
            "proxy_id": proxy_id,
            "new_profile_tags": [],
            "profile_status": None,
            "browser": browser,
            "platform": platform,
            "fingerprint": fingerprint,
        }

        data = await self.session.post(self.public_api_endpoint + f"/folders/{folder_id}/profiles", json=body)
        return Profile.load(data["data"])
