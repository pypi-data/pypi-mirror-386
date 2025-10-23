from typing import Any
from uuid import UUID

from ..models import Folder, RunningProfile, Profile, Proxy

# Precomputed hex set for fast membership checks
_HEX = set("0123456789abcdefABCDEF")


def _is_uuid4_fast(s: str) -> bool:
    """
    Fast UUID4 string validation.

    Checks:
    - Length is 36
    - Dashes at 8, 13, 18, 23
    - All other chars are hex
    - Version nibble '4' at index 14
    - Variant nibble in {'8','9','a','b','A','B'} at index 19

    :param s: Candidate string.

    :returns: True if s is a valid UUID4, else False.
    """
    if len(s) != 36:
        return False

    if s[8] != "-" or s[13] != "-" or s[18] != "-" or s[23] != "-":
        return False

    if s[14] != "4":
        return False

    v = s[19]
    if v not in ("8", "9", "a", "b", "A", "B"):
        return False

    for i, ch in enumerate(s):
        if i in (8, 13, 18, 23):
            continue
        if ch not in _HEX:
            return False

    return True


def extract_folder_id(obj: Folder | UUID | str | Any) -> str:
    """
    Extract folder id and validate it is UUID4.

    :param obj: Folder instance or string-like identifier.

    :returns: The original folder id string if it is a valid UUID4.
    :raises ValueError: If the result is not a valid UUID4.
    """
    if isinstance(obj, Folder):
        folder_id = obj.id
    else:
        folder_id = str(obj)

    if not _is_uuid4_fast(folder_id):
        raise ValueError(
            f"Folder id must be a UUID4 string, got {folder_id!r} "
            f"(from {type(obj).__name__})"
        )

    return folder_id


def extract_profile_id(obj: Profile | RunningProfile | UUID | str | Any) -> str:
    """
    Extract profile id and validate it is UUID4.

    :param obj: Profile, RunningProfile or string-like identifier.

    :returns: The original profile id string if it is a valid UUID4.
    :raises ValueError: If the result is not a valid UUID4.
    """
    if isinstance(obj, Profile):
        profile_id = obj.id
    elif isinstance(obj, RunningProfile):
        profile_id = obj.profile_id
    else:
        profile_id = str(obj)

    if not _is_uuid4_fast(profile_id):
        raise ValueError(
            f"Profile id must be a UUID4 string, got {profile_id!r} "
            f"(from {type(obj).__name__})"
        )

    return profile_id

def extract_proxy_id(obj: Proxy | UUID | str | Any) -> str:
    """
    Extract proxy id and validate it is UUID4.

    :param obj: Proxy instance or string-like identifier.

    :returns: The original proxy id string if it is a valid UUID4.
    :raises ValueError: If the result is not a valid UUID4.
    """
    if isinstance(obj, Proxy):
        proxy_id = obj.id
    else:
        proxy_id = str(obj)

    if not _is_uuid4_fast(proxy_id):
        raise ValueError(
            f"Proxy id must be a UUID4 string, got {proxy_id!r} "
            f"(from {type(obj).__name__})"
        )

    return proxy_id

def extract_proxy_ids(proxy_ids: list[Proxy | UUID | str | Any]) -> list[str]:
    """
    Extract and validate a list of proxy ids as UUID4 strings.

    The function:
    - accepts a list of Proxy instances or arbitrary values;
    - converts each item to an id string (``Proxy.id`` or ``str(item)``);
    - strips blanks and skips empty results;
    - validates each id as UUID4;
    - de-duplicates while preserving order.

    :param proxy_ids: List of Proxy objects or id-like values.

    :returns: List of unique UUID4 strings.
    :raises ValueError: If the input list is empty after normalization or
                        any item is not a valid UUID4 string.
    """
    if not isinstance(proxy_ids, list):
        raise ValueError(
            f"proxy_ids must be a list, got {type(proxy_ids).__name__}"
        )

    collected = []
    for idx, item in enumerate(proxy_ids):
        if isinstance(item, Proxy):
            s = str(item.id).strip()
        else:
            s = str(item).strip()

        if not s:
            # Skip empty/whitespace-only items silently
            continue

        if not _is_uuid4_fast(s):
            raise ValueError(
                f"Invalid proxy id at index {idx}: {s!r} "
                f"(from {type(item).__name__}); must be UUID4 string"
            )

        collected.append(s)

    if not collected:
        raise ValueError("proxy_ids must contain at least one valid UUID4 id")

    seen = set()
    uniq_ids = []
    for s in collected:
        if s not in seen:
            seen.add(s)
            uniq_ids.append(s)

    return uniq_ids

def resolve_folder_and_profile_ids(
    profile: Profile | RunningProfile | UUID | str,
    folder: Folder | UUID | str | None = None,
) -> tuple[str, str]:
    """
    Resolve (folder_id, profile_id) pair from given arguments.

    Either:
    - profile is Profile/RunningProfile (folder may be None), or
    - profile and folder are id-like values.

    :param profile: Profile object, RunningProfile object, UUID, or string.
    :param folder: Folder object, UUID, or string, required if ``profile``
                   does not carry folder_id.

    :returns: Tuple (folder_id, profile_id) as UUID4 strings.
    :raises ValueError: If arguments combination is invalid.
    """
    if folder is None:
        if isinstance(profile, Profile):
            folder_id, profile_id = str(profile.folder_id), str(profile.id)
        elif isinstance(profile, RunningProfile):
            folder_id, profile_id = str(profile.folder_id), str(profile.profile_id)
        else:
            raise ValueError(
                f"When folder is None, 'profile' must be Profile or RunningProfile, "
                f"got {type(profile).__name__}"
            )
    else:
        folder_id = extract_folder_id(folder)
        profile_id = extract_profile_id(profile)

    return folder_id, profile_id