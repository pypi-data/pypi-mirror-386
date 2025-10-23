from datetime import datetime

from ..base import BaseModel


class Proxy(BaseModel):
    """
    Proxy record returned by public API.
    """

    user_id: str
    id: str
    folder_id: str

    proxy_name: str
    proxy_type: str
    proxy_ip: str
    proxy_port: int

    proxy_username: str | None = None
    proxy_password: str | None = None
    update_url: str | None = None

    # API variants: some payloads use "geo_info", docs mention "proxy_geo".
    geo_info: dict | None = None
    proxy_geo: dict | None = None

    last_check_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # May be null or an array depending on endpoint.
    profiles: list[str] | int | None = None
