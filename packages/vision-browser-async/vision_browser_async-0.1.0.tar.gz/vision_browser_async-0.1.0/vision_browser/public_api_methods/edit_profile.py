from uuid import UUID

from ..base import BaseAPIMethod
from ..models import Folder, Profile, Proxy, RunningProfile
from ..utils.validators import resolve_folder_and_profile_ids


class EditProfile(BaseAPIMethod):
    async def _execute_impl(
            self,
            profile: Profile | RunningProfile | UUID | str | None = None,
            profile_name: str | None = None,
            profile_notes: str | None = None,
            profile_tags: list[str] | None = None,
            new_profile_tags: list[str] | None = None,
            profile_status: str | None = None,
            pinned: bool | None = None,
            proxy_id: Proxy | UUID | str | None = None,
            folder_id: Folder | UUID | str | None = None,
    ) -> Profile:
        folder_id, profile_id = resolve_folder_and_profile_ids(profile, folder_id)

        # Construct partial body with only provided keys.
        body: dict = {}

        if profile_name is not None:
            body["profile_name"] = profile_name
        if profile_notes is not None:
            body["profile_notes"] = profile_notes
        if profile_tags is not None:
            body["profile_tags"] = profile_tags
        if new_profile_tags is not None:
            body["new_profile_tags"] = new_profile_tags
        if profile_status is not None:
            body["profile_status"] = profile_status
        if pinned is not None:
            body["pinned"] = bool(pinned)

        # Proxy handling:
        # API docs show `"proxy_id": "none" | Proxy`, where Proxy has `{ "id": UUID }`.
        if proxy_id is not None:
            if isinstance(proxy_id, Proxy):
                body["proxy_id"] = {"id": proxy_id.id}
            else:
                s = str(proxy_id).strip()
                if not s:
                    # Empty string means "no change" — omit key.
                    pass
                elif s.lower() == "none":
                    body["proxy_id"] = "none"
                else:
                    # Accept a raw UUID string by wrapping it as Proxy type object.
                    body["proxy_id"] = {"id": s}

        url = self.public_api_endpoint + f"/folders/{folder_id}/profiles/{profile_id}"
        payload = await self.session.patch(url, json=body)

        container = payload.get("data") if isinstance(payload, dict) and "data" in payload else payload
        return Profile.load(container)
