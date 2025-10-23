import asyncio
import logging
import random
from json import JSONDecodeError
from typing import TypedDict, Unpack

import httpx
from httpx import Proxy, URL

from .utils import parse_retry_after
from ..errors import raise_from_response

logger = logging.getLogger(__name__)


class RequestOptions(TypedDict, total=False):
    """
    Common per-request options.

    :param params: Query params in any httpx-compatible form.
    :param headers: Extra per-request headers.
    :param json: JSON body or any JSON-serializable object.
    :param retries: Override default retry count for this call.
    """
    params: dict | list[tuple[str, str]] | tuple | str | bytes | None
    headers: dict[str, str] | None
    json: object | None
    retries: int | None


# noinspection PyIncorrectDocstring
class HttpSession:
    """
    Async HTTP session with retries, backoff, and minimal logging.

    :param headers: Default headers for the session.
    :param proxy: Proxy URL or httpx Proxy object.
    :param timeout: Request timeout in seconds or httpx.Timeout.
    :param follow_redirects: Whether to follow redirects.
    :param retries: Number of retry attempts for transient failures.
    :param backoff_base: Base delay for exponential backoff in seconds.
    :param max_backoff: Maximum backoff delay in seconds.
    :param retry_statuses: Deprecated. Retrying on status is handled in exceptions now.

    :returns: Configured HttpSession instance.
    """

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        proxy: URL | str | Proxy | None = None,
        timeout: float | httpx.Timeout | None = 30.0,
        follow_redirects: bool = True,
        retries: int = 3,
        backoff_base: float = 0.5,
        max_backoff: float = 10.0,
        retry_statuses: set[int] | None = None,
    ):
        self.client = httpx.AsyncClient(
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )
        self.retries = retries
        self.backoff_base = backoff_base
        self.max_backoff = max_backoff
        # Kept for backward compatibility; not used anymore.
        self.retry_statuses = retry_statuses or set()

    async def aclose(self) -> None:
        """
        Close the underlying client.

        :returns: None.
        """
        await self.client.aclose()

    def _compute_backoff(self, attempt: int, retry_after: float | None) -> float:
        """
        Compute backoff delay for a given attempt.

        :param attempt: Attempt number starting at 1.
        :param retry_after: Parsed Retry-After seconds, if present.

        :returns: Backoff delay in seconds.
        """
        if retry_after is not None:
            return min(self.max_backoff, max(0.0, retry_after))
        exp = self.backoff_base * (2 ** (attempt - 1))
        return min(self.max_backoff, random.uniform(0.0, exp))

    async def request(
        self,
        method: str,
        url: str,
        json=None,
        params: dict | list[tuple[str, str]] | tuple | str | bytes | None = None,
        headers: dict[str, str] | None = None,
        retries: int | None = None,
    ):
        """
        Perform an HTTP request with retries and backoff.

        :param method: HTTP method name like "GET" or "POST".
        :param url: Full URL or relative if client has base_url.
        :param json: JSON body or any JSON-serializable object.
        :param params: Query params in any httpx-compatible form.
        :param headers: Extra per-request headers.
        :param retries: Override default retry count for this call.

        :returns: Parsed JSON (object) or response text (str).

        :raises httpx.TimeoutException: On persistent timeouts.
        :raises httpx.TransportError: On persistent transport errors.
        :raises httpx.HTTPStatusError: On non-OK final status after retry policy.
        :raises RuntimeError: If the retry loop exits unexpectedly.
        """
        if isinstance(params, dict):
            params = {k: v for k, v in params.items() if v is not None}

        max_attempts = (retries if retries is not None else self.retries) + 1

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(
                    "HTTP %s %s | attempt=%s | has_params=%s | has_json=%s | has_headers=%s",
                    method, url, attempt, bool(params), bool(json), bool(headers),
                )

                response = await self.client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=headers,
                )

                try:
                    data = response.json()
                    raise_from_response(data)
                except JSONDecodeError:
                    data = response.text

                response.raise_for_status()
                return data

            except httpx.ConnectError:
                raise ConnectionError("Could not connect to a Vision app. Make sure it's running")

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt < max_attempts:
                    delay = self._compute_backoff(attempt, None)
                    logger.warning(
                        "Network error on %s %s: %s; retrying in %.2fs (attempt %d/%d)",
                        method, url, exc, delay, attempt, max_attempts - 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error("Giving up after %d attempts on %s %s", attempt, method, url)
                raise

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if 400 <= status < 500:
                    logger.error(
                        "Client error %s on %s %s; not retrying",
                        status, method, exc.request.url,
                    )
                    raise
                if 500 <= status < 600 and attempt < max_attempts:
                    retry_after = None
                    if ra := exc.response.headers.get("Retry-After"):
                        retry_after = parse_retry_after(ra)
                    delay = self._compute_backoff(attempt, retry_after)
                    logger.warning(
                        "Server error %s for %s %s; retrying in %.2fs (attempt %d/%d)",
                        status, method, exc.request.url, delay, attempt, max_attempts - 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(
                    "HTTP error %s on %s %s; giving up",
                    status, method, exc.request.url,
                )
                raise

        raise RuntimeError("Unreachable: request loop exited without return or raise")

    async def get(self, url: str, **options: Unpack[RequestOptions]):
        return await self.request("GET", url, **options)

    async def post(self, url: str, **options: Unpack[RequestOptions]):
        return await self.request("POST", url, **options)

    async def put(self, url: str, **options: Unpack[RequestOptions]):
        return await self.request("PUT", url, **options)

    async def patch(self, url: str, **options: Unpack[RequestOptions]):
        return await self.request("PATCH", url, **options)

    async def delete(self, url: str, **options: Unpack[RequestOptions]):
        return await self.request("DELETE", url, **options)
