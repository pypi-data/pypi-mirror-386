from urllib.parse import urlsplit


def proxy_to_payload(raw: str) -> dict:
    """
    Parse a proxy string into API payload.

    :param raw: Source proxy string.
    :param seq: Sequential number for default naming.

    :returns: Dict payload acceptable by the API.
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Empty proxy string")

    # Try URL-style first. If there's no scheme, temporarily add http:// for parsing.
    s = raw
    added_scheme = False
    if "://" not in s and "@" in s:
        s = "http://" + s
        added_scheme = True

    host = ""
    port = None
    user = None
    pwd = None
    ptype = None

    if "://" in s:
        parts = urlsplit(s)
        # Determine type from scheme unless we injected it.
        if not added_scheme:
            ptype = scheme_to_type(parts.scheme)
        # Extract auth and host/port.
        netloc = parts.netloc
        if "@" in netloc:
            creds, _, hostport = netloc.rpartition("@")
            if ":" in creds:
                user, _, pwd = creds.partition(":")
            else:
                user = creds or None
            host, port = split_host_port(hostport)
        else:
            host, port = split_host_port(netloc)
    else:
        # Non-URL forms:
        # 1) host:port:user:pass
        # 2) host:port
        # 3) user:pass@host:port
        if "@" in raw:
            creds, _, hostport = raw.rpartition("@")
            if ":" in creds:
                user, _, pwd = creds.partition(":")
            else:
                user = creds or None
            host, port = split_host_port(hostport)
        else:
            parts = raw.split(":")
            if len(parts) == 4:
                host, port_s, user, pwd = parts
                port = port_to_int(port_s)
            elif len(parts) == 2:
                host, port_s = parts
                port = port_to_int(port_s)
            else:
                raise ValueError(f"Unsupported proxy format: {raw!r}")

    if not host or port is None:
        raise ValueError(f"Missing host/port in proxy: {raw!r}")

    if ptype is None:
        # Default to SOCKS5 if type is unknown.
        ptype = "SOCKS5"

    name = f"{ptype} {host}:{port}"

    return {
        "proxy_name": name,
        "proxy_type": ptype,
        "proxy_ip": host,
        "proxy_port": port,
        "proxy_username": user,
        "proxy_password": pwd,
        # "update_url": None,  # leave out if not provided; session will strip Nones
    }

def scheme_to_type(scheme: str) -> str:
    """
    Map URL scheme to API proxy_type.

    :param scheme: Parsed URL scheme.

    :returns: One of HTTP, SOCKS4, SOCKS5, SSH (default SOCKS5 for socks/socks5h).
    """
    s = (scheme or "").lower()
    if s in ("http", "https"):
        return "HTTP"
    if s in ("socks4", "socks4a"):
        return "SOCKS4"
    if s in ("socks", "socks5", "socks5h"):
        return "SOCKS5"
    if s == "ssh":
        return "SSH"
    return "SOCKS5"

def port_to_int(value: str) -> int:
    """
    Convert a numeric string to int with validation.

    :param value: Source string.

    :returns: Integer value.
    """
    v = int(value.strip())
    if v <= 0 or v > 65535:
        raise ValueError(f"Invalid port {v}")
    return v

def split_host_port(hostport: str) -> tuple[str, int]:
    """
    Split host:port, trimming brackets if present.

    :param hostport: String in form host:port.

    :returns: (host, port)
    """
    hp = hostport.strip().lstrip("[").rstrip("]")
    if ":" not in hp:
        raise ValueError(f"Port missing in {hostport!r}")
    host, _, port_s = hp.rpartition(":")
    return host.strip(), port_to_int(port_s)

