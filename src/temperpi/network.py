"""Look up the Pi's IPv4 address for display (Linux only, stdlib only)."""

from __future__ import annotations

import fcntl
import socket
import struct
from collections.abc import Iterable

_SIOCGIFADDR = 0x8915
NO_IPV4 = "No IPv4!"


def interface_ipv4(name: str) -> str | None:
    """Return the IPv4 address assigned to ``name``, or None."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            packed = fcntl.ioctl(
                sock.fileno(), _SIOCGIFADDR, struct.pack("256s", name[:15].encode())
            )
        except OSError:
            return None
    return socket.inet_ntoa(packed[20:24])


def primary_ipv4(preferred: Iterable[str] = ("eth0", "end0", "wlan0")) -> str:
    """Address of the first preferred interface that has one, else any non-loopback."""
    preferred = list(preferred)
    others = sorted(name for _, name in socket.if_nameindex() if name not in preferred)
    for name in [*preferred, *others]:
        if name == "lo":
            continue
        addr = interface_ipv4(name)
        if addr and not addr.startswith("127."):
            return addr
    return NO_IPV4
