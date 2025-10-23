# F:\Developing\python\_freelance\vfsglobal-browser\browser_vision\vision_api.py
from typing import Literal, Self
from uuid import UUID

from .http_session import HttpSession
from .local_api_methods import ListRunningProfiles, StartProfile, StopProfile
from .models import RunningProfile, Folder, Profile, Fingerprint, Proxy
from .public_api_methods import (
    ListFolders,
    ListProfiles,
    GetProfileByName,
    GetFingerprint,
    DeleteProfile,
    CreateProfile,
    CreateProxies,
    ListProxies,
    DeleteProxies,
    FindProxiesByUrl,
    CreateFolder,
    GetFolderByName,
    EditProfile,
)
from .types import FolderIcon, FolderColor


class VisionAPI:
    """
    High-level client for Vision's local and public APIs.

    Provides a thin async wrapper over method objects in ``local_api_methods`` and
    ``public_api_methods`` namespaces and exposes a shared HTTP session with retries.
    """

    LOCAL_API_ENDPOINT = "http://127.0.0.1:3030"
    PUBLIC_API_ENDPOINT = "https://v1.empr.cloud/api/v1"

    def __init__(self, token: str, local_api_endpoint: str | None = None, public_api_endpoint: str | None = None):
        """
        Initialize the Vision API client.

        :param token: API token passed as ``X-Token`` header for public endpoints.
        :param local_api_endpoint: Optional override for local API base URL.
        :param public_api_endpoint: Optional override for public API base URL.

        :returns: None.
        """
        self.token = token
        self._local_api_endpoint = local_api_endpoint
        self._public_api_endpoint = public_api_endpoint
        self.session = HttpSession(headers={"X-Token": token})

    async def __aenter__(self) -> Self:
        """
        Enter async context and return the client.

        This method does not perform network I/O. The shared HTTP session is
        already constructed in ``__init__``.

        :returns: Self.
        """
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Exit async context and close the underlying HTTP session.

        Always attempts to close the session regardless of an exception.

        :param exc_type: Exception type if one occurred.
        :param exc: Exception instance if one occurred.
        :param tb: Traceback if one occurred.

        :returns: None.
        """
        await self.session.aclose()

    @property
    def local_api_endpoint(self):
        """
        Resolve the local API base URL.

        :returns: Effective local API endpoint string.
        """
        return self._local_api_endpoint or self.LOCAL_API_ENDPOINT

    @property
    def public_api_endpoint(self):
        """
        Resolve the public API base URL.

        :returns: Effective public API endpoint string.
        """
        return self._public_api_endpoint or self.PUBLIC_API_ENDPOINT

    # Local API methods

    async def list_running_profiles(self) -> list[RunningProfile]:
        """
        List running profiles from the local API.

        :returns: List of running profile descriptors.
        """
        return await ListRunningProfiles(self).execute()

    async def start_profile(
            self,
            profile: Profile,
            args: list[str] | None = None,
            wait_until_started: bool | None = None,
    ) -> RunningProfile:
        """
        Start a profile via the local API.

        :param profile: Profile to start.
        :param args: Optional list of extra launch arguments.
        :param wait_until_started: If True, poll local API until a listening port appears.

        :returns: ``RunningProfile`` description with listening port if available.
        """
        return await StartProfile(self).execute(profile, args, wait_until_started)

    async def stop_profile(self, profile: Profile | RunningProfile, wait_until_close: bool | None = None):
        """
        Stop a running profile via the local API.

        :param profile: Target profile (``Profile`` or ``RunningProfile``).
        :param wait_until_close: If True, wait until the profile disappears from the list.

        :returns: None.
        """
        return await StopProfile(self).execute(profile, wait_until_close)

    async def raise_if_local_api_not_running(self):
        """
        Raise if local API is not reachable.

        :returns: None.
        """
        await self.list_running_profiles()

    # Public API methods

    async def list_folders(self) -> list[Folder]:
        """
        Fetch all folders for the current user.

        :returns: List of folders.
        """
        return await ListFolders(self).execute()

    async def list_profiles(self, folder_id: Folder | UUID | str, name: str | None = None) -> list[Profile]:
        """
        List profiles in a folder with automatic pagination.

        :param folder_id: Folder ID, ``UUID``, or ``Folder`` instance.
        :param name: Optional case-insensitive substring filter for profile name.

        :returns: All profiles matching the criteria.
        """
        return await ListProfiles(self).execute(folder_id, name)

    async def get_profile_by_name(self, profile_name: str, folder_id: Folder | str | None = None) -> Profile | None:
        """
        Find the first profile by exact name.

        Searches the given folder if provided; otherwise scans all folders.

        :param profile_name: Target profile name (exact match).
        :param folder_id: Optional folder (instance or ID) to restrict the search.

        :returns: ``Profile`` if found, else ``None``.
        """
        return await GetProfileByName(self).execute(profile_name, folder_id)

    async def get_fingerprint(self, platform: Literal["macos", "windows", "linux"],
                              version: int | None = None) -> Fingerprint:
        """
        Retrieve a browser fingerprint descriptor.

        :param platform: Target platform, one of ``"macos"``, ``"windows"``, ``"linux"``.
        :param version: Specific major version or ``None`` to use ``latest``.

        :returns: ``Fingerprint`` model.
        """
        return await GetFingerprint(self).execute(platform, version)

    async def create_profile(
            self,
            folder_id: Folder | UUID | str,
            profile_name: str,
            profile_notes: str | None = None,
            profile_tags: list[str] | None = None,
            proxy_id: Proxy | UUID | str | None = None,
            profile_status: list[tuple[str, str] | None] = None,
            platform: Literal["Windows", "Mac", "Linux"] | None = None,
            browser: Literal["Chrome"] | None = None,
            fingerprint: Fingerprint | None = None,
            webrtc_pref: dict | Literal["auto", "off"] | None = None,
            webgl_pref: Literal["real", "off"] | dict | float | None = None,
            canvas_pref: Literal["real", "off"] | dict | float | None = None,
            ports_protection: list[int] | None = None,
    ) -> Profile | None:
        """
        Create a new profile in a folder.

        Notes on preferences:
        - ``webrtc_pref`` accepts a dict (e.g. manual settings) or ``"auto"``/``"off"``.
        - ``webgl_pref`` accepts ``"real"``/``"off"`` or an object ``{"noise": <float>}``.
          For convenience, if a plain ``float`` is passed, it will be wrapped as
          ``{"noise": round(value, 8)}`` to satisfy API requirements (8 decimal places).
        - ``canvas_pref`` accepts ``"real"``/``"off"`` or an object ``{"noise": <float>}``.
          A plain ``float`` will be wrapped similarly to WebGL.

        :param folder_id: Folder ID, ``UUID``, or ``Folder`` instance.
        :param profile_name: Profile display name.
        :param profile_notes: Optional notes.
        :param profile_tags: Optional list of tags.
        :param proxy_id: Proxy object/ID or ``None``.
        :param profile_status: Optional status payload as a list of key/value tuples.
        :param platform: Target platform (``"Windows"``, ``"Mac"``, ``"Linux"``).
        :param browser: Browser engine (currently ``"Chrome"``).
        :param fingerprint: Fingerprint model to seed profile.
        :param webrtc_pref: WebRTC preference settings.
        :param webgl_pref: WebGL preference settings (``"real"``, ``"off"``, or noise).
        :param canvas_pref: Canvas preference settings (``"real"``, ``"off"``, or noise).
        :param ports_protection: Optional list of ports to protect.

        :returns: Created ``Profile`` or ``None`` depending on backend response.
        """
        # Normalize "noise" floats to dicts with 8 decimal places as required by API.
        if isinstance(webgl_pref, float):
            webgl_pref = {"noise": round(webgl_pref, 8)}
        if isinstance(canvas_pref, float):
            canvas_pref = {"noise": round(canvas_pref, 8)}

        return await CreateProfile(self).execute(
            folder_id=folder_id,
            profile_name=profile_name,
            profile_notes=profile_notes,
            profile_tags=profile_tags,
            proxy_id=proxy_id,
            profile_status=profile_status,
            platform=platform,
            browser=browser,
            fingerprint=fingerprint,
            webrtc_pref=webrtc_pref,
            webgl_pref=webgl_pref,
            canvas_pref=canvas_pref,
            ports_protection=ports_protection,
        )

    async def edit_profile(
            self,
            profile: Profile | RunningProfile | UUID | str,
            *,
            profile_name: str | None = None,
            profile_notes: str | None = None,
            profile_tags: list[str] | None = None,
            new_profile_tags: list[str] | None = None,
            profile_status: str | None = None,
            pinned: bool | None = None,
            proxy_id: Proxy | UUID | str | None = None,
            folder_id: Folder | UUID | str | None = None,
    ) -> Profile:
        """
        Partially update an existing profile.

        Omitted keyword arguments are not modified. For ``proxy_id``:
        - Pass a ``Proxy`` instance to set that proxy.
        - Pass a non-empty UUID string or ``UUID`` to set by ID.
        - Pass ``"none"`` (case-insensitive) to detach the proxy.
        - Pass ``None`` to keep the current value.

        :param profile: Target profile (object or id-like).
        :param profile_name: New name.
        :param profile_notes: New notes.
        :param profile_tags: Full tag list replacement.
        :param new_profile_tags: Tags to add.
        :param profile_status: New status string.
        :param pinned: Pin/unpin flag.
        :param proxy_id: Proxy to assign, raw ID/UUID, ``"none"``, or ``None``.
        :param folder_id: Destination folder (ID/UUID or instance), defaults to current.

        :returns: Updated ``Profile``.
        """
        return await EditProfile(self).execute(
            profile=profile,
            profile_name=profile_name,
            profile_notes=profile_notes,
            profile_tags=profile_tags,
            new_profile_tags=new_profile_tags,
            profile_status=profile_status,
            pinned=pinned,
            proxy_id=proxy_id,
            folder_id=folder_id,
        )

    async def create_folder(
            self,
            folder_name: str,
            folder_icon: FolderIcon | str | None = None,
            folder_color: FolderColor | str | None = None,
    ) -> Folder:
        """
        Create a new folder.

        If ``folder_icon`` or ``folder_color`` is omitted, the first allowed value
        from the corresponding ``Literal`` union is used.

        :param folder_name: Folder display name.
        :param folder_icon: Icon name from ``FolderIcon`` or custom string.
        :param folder_color: Color token from ``FolderColor`` or custom string.

        :returns: Created ``Folder``.
        """
        return await CreateFolder(self).execute(folder_name, folder_icon, folder_color)

    async def get_folder_by_name(self, folder_name: str) -> Folder | None:
        """
        Find a folder by exact name.

        :param folder_name: Target folder name (exact match).

        :returns: ``Folder`` if found, else ``None``.
        """
        return await GetFolderByName(self).execute(folder_name)

    async def delete_profile(
            self,
            profile: Profile | RunningProfile | UUID | str,
            folder: Folder | UUID | str | None = None,
    ) -> Profile | str | None:
        """
        Delete a profile.

        You can call it either with a single argument (``Profile`` or ``RunningProfile``),
        where the folder is obtained from the object, or with two arguments
        (``profile`` id/object and ``folder`` id/object).

        :param profile: Profile/RunningProfile object or id-like value.
        :param folder: Folder object or id-like value. Required if ``profile`` does not
                       carry ``folder_id`` (i.e. when passing a plain ID/UUID/string).

        :returns: Server message string, a ``Profile`` (depending on backend usage semantics),
                  or ``None``.
        """
        return await DeleteProfile(self).execute(profile, folder)

    async def list_proxies(self, folder_id: Folder | UUID | str) -> list[Proxy]:
        """
        List proxies in a folder.

        :param folder_id: Folder ID/UUID or ``Folder`` instance.

        :returns: List of ``Proxy`` records.
        """
        return await ListProxies(self).execute(folder_id)

    async def create_proxies(self, folder_id: Folder | UUID | str, proxies: list[str]) -> list[Proxy]:
        """
        Create multiple proxies from raw strings.

        Supported formats include URL-like strings (e.g. ``http://user:pass@host:port``)
        and common shorthand notations.

        :param folder_id: Folder ID/UUID or ``Folder`` instance.
        :param proxies: List of raw proxy strings.

        :returns: List of created ``Proxy`` records.
        """
        return await CreateProxies(self).execute(folder_id, proxies)

    async def create_proxy(self, folder_id: Folder | UUID | str, proxy: str) -> Proxy:
        """
        Convenience helper to create a single proxy.

        :param folder_id: Folder ID/UUID or ``Folder`` instance.
        :param proxy: Raw proxy string.

        :returns: Created ``Proxy``.
        """
        return (await CreateProxies(self).execute(folder_id, [proxy]))[0]

    async def delete_proxies(self, folder_id: Folder | UUID | str, proxy_ids: list[str] | list[Proxy]) -> list[Proxy]:
        """
        Delete proxies by IDs or ``Proxy`` objects.

        :param folder_id: Folder ID/UUID or ``Folder`` instance.
        :param proxy_ids: Mixed list of raw IDs/UUID strings and/or ``Proxy`` instances.

        :returns: List of deleted ``Proxy`` records reported by the backend.
        """
        return await DeleteProxies(self).execute(folder_id, proxy_ids)

    async def find_proxies_by_url(self, folder_id: Folder | UUID | str, url: str) -> list[Proxy]:
        """
        Find proxies in a folder that match a given URL representation.

        The URL is parsed into a canonical proxy payload and compared against
        stored proxies by type, host, port, and credentials.

        :param folder_id: Folder ID/UUID or ``Folder`` instance.
        :param url: Proxy URL or shorthand to match against.

        :returns: Matching proxies.
        """
        return await FindProxiesByUrl(self).execute(folder_id, url)
