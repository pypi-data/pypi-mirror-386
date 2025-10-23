from ..base import BaseAPIMethod
from ..models import Folder, Proxy
from ..utils.proxy import proxy_to_payload


class FindProxiesByUrl(BaseAPIMethod):
    async def _execute_impl(self, folder_id: Folder | str, url: str) -> list[Proxy]:
        proxies = await self.vision_api.list_proxies(folder_id)
        proxy_payload = proxy_to_payload(url)
        found_proxies = []
        for proxy in proxies:
            if all((
                    proxy.proxy_type == proxy_payload["proxy_type"],
                    proxy.proxy_ip == proxy_payload["proxy_ip"],
                    proxy.proxy_port == proxy_payload["proxy_port"],
                    proxy.proxy_username == proxy_payload["proxy_username"],
                    proxy.proxy_password == proxy_payload["proxy_password"],
            )):
                found_proxies.append(proxy)
        return found_proxies
