from ..base import BaseModel


class RunningProfile(BaseModel):
    folder_id: str
    profile_id: str
    port: int | None = None
