from datetime import datetime, UTC
from email.utils import parsedate_to_datetime


def parse_retry_after(value: str) -> float | None:
    """
    Parse the Retry-After header value.

    Supports both delta-seconds and HTTP-date formats.

    :param value: Raw Retry-After header value.

    :returns: Delay in seconds, or None if unparseable.
    """
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        return float(int(value))
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    delta = (dt - datetime.now(UTC)).total_seconds()
    return max(0.0, delta)