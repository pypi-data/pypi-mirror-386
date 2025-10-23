from datetime import datetime

from ..base import BaseModel


class Folder(BaseModel):
    id: str
    owner: str
    folder_name: str
    folder_icon: str
    folder_color: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
