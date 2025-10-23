from datetime import datetime

from ..base import BaseModel


class Profile(BaseModel):
    owner: str
    id: str
    folder_id: str
    proxy_id: str | None
    profile_name: str
    profile_notes: str
    profile_status: str | None
    profile_tags: list[str]
    browser: str
    platform: str
    running: bool
    pinned: bool
    worktime: int
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
    recovered: int
    is_received: bool
    app_version: str
    proxy: dict | None