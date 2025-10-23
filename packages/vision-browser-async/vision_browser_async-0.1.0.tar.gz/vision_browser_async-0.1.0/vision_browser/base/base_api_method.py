from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..vision_api import VisionAPI


class BaseAPIMethod(abc.ABC):
    """
    Common base for API method objects.

    Holds a reference to the high-level ``VisionAPI`` client and exposes
    its HTTP session and endpoint helpers to subclasses.
    """

    def __init__(self, vision_api: VisionAPI):
        """
        Initialize the API method.

        :param vision_api: Root client object providing session and endpoints.

        :returns: None.
        """
        self.vision_api = vision_api

        # Shortcuts
        self.session = vision_api.session

    @property
    def local_api_endpoint(self) -> str:
        """
        Local (on-device/app) API base URL.

        :returns: Base URL string for local API calls.
        """
        return self.vision_api.local_api_endpoint

    @property
    def public_api_endpoint(self) -> str:
        """
        Public (cloud) API base URL.

        :returns: Base URL string for public API calls.
        """
        return self.vision_api.public_api_endpoint

    async def execute(self, *args, **kwargs):
        """
        Run the concrete API method.

        Delegates to ``_execute_impl`` implemented by subclasses.

        :param args: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.

        :returns: Subclass-defined result.
        """
        return await self._execute_impl(*args, **kwargs)

    @abc.abstractmethod
    async def _execute_impl(self, *args, **kwargs):
        """
        Concrete implementation of the API call.

        Subclasses must implement this coroutine and perform all network I/O,
        parsing, and error handling.

        :param args: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.

        :returns: Method-specific result.
        """
        raise NotImplementedError("Subclasses must implement _execute_impl()")
