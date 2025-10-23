<p align="center">
  <img src="https://browser.vision/_next/image?url=%2Ficons%2Flogo.svg&amp;w=256&amp;q=75" alt="Vision Browser logo" width="164">
</p>

<p align="center">
  <a href="https://pypi.org/project/vision-browser-async/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/vision-browser-async.svg">
  </a>
  <a href="https://pypi.org/project/vision-browser-async/">
    <img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/vision-browser-async.svg">
  </a>
  <a href="https://github.com/diprog/vision-browser">
    <img alt="Repository" src="https://img.shields.io/badge/source-github-black">
  </a>
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg">
  </a>
</p>

# vision-browser

Async client for the Vision browser automation platform. The library wraps both the local Vision app API and the public cloud API, providing Pydantic models and retrying HTTP access powered by `httpx`.

## Features
- Async wrapper around Vision local (`127.0.0.1:3030`) and public (`https://v1.empr.cloud/api/v1`) endpoints
- Ready-to-use Pydantic models for profiles, folders, proxies, fingerprints and running sessions
- Automatic retries with exponential backoff for transient HTTP failures
- Helper utilities for validating IDs, preparing proxy payloads and generating noise preferences

## Requirements
- Python 3.13+
- Vision desktop application running locally for local API calls
- Vision API token for public endpoints

## Installation
```bash
pip install vision-browser-async
```
The package targets Python 3.13 and newer. Older interpreters are not supported. The installed module keeps the original import path (`vision_browser`).

## Quick start
```python
import asyncio
from vision_browser import VisionAPI


async def main() -> None:
    token = "your-api-token"
    async with VisionAPI(token) as client:
        folders = await client.list_folders()
        default_folder = folders[0]

        # Create a profile using the public API
        fingerprint = await client.get_fingerprint(platform="windows")
        profile = await client.create_profile(
            folder_id=default_folder.id,
            profile_name="Sample profile",
            fingerprint=fingerprint,
            platform="Windows",
            browser="Chrome",
        )

        # Start the profile through the local API
        running = await client.start_profile(profile)
        print(f"{running.profile_name} is running on port {running.port}")

        await client.stop_profile(running)


if __name__ == "__main__":
    asyncio.run(main())
```

## Available API helpers
- `vision_browser.public_api_methods` covers CRUD for folders, profiles, proxies and fingerprint retrieval.
- `vision_browser.local_api_methods` exposes start/stop operations for profiles running in the local Vision application.
- `vision_browser.utils` contains helpers for ID validation, proxy parsing and noise preference generation.
- `vision_browser.errors` provides the base `VisionBrowserAPIError` raised when Vision responds with an error payload.

Refer to the module docstrings for detailed argument descriptions and return types.

## Development and publishing
Build and upload distributions using [build](https://pypi.org/project/build/) and [twine](https://pypi.org/project/twine/):
```bash
python -m build
twine check dist/*
twine upload dist/*
```

## License
Released under the [MIT License](LICENSE).
