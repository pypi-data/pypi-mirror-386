import base64
from typing import List

from datetime import datetime, timezone
from typing import Optional
import random
import string


def zero_datetime() -> datetime:
    return datetime.fromtimestamp(0, timezone.utc)


def timestamp_to_datetime(ts: Optional[int]) -> Optional[datetime]:
    return datetime.fromtimestamp(ts) if ts else None


def datetime_to_timestamp(dt: Optional[datetime]) -> Optional[int]:
    return int(dt.timestamp()) if dt else None


def randstr(length=6) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def b64_encode(s: bytes) -> str:
    """Encode bytes into a URL-safe Base64 string without padding

    Parameters:
        s (``bytes``):
            Bytes to encode

    Returns:
        ``str``: The encoded bytes
    """
    return base64.urlsafe_b64encode(s).decode().strip("=")


def b64_decode(s: str) -> bytes:
    """Decode a URL-safe Base64 string without padding to bytes

    Parameters:
        s (``str``):
            String to decode

    Returns:
        ``bytes``: The decoded string
    """
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def rle_encode(s: bytes) -> bytes:
    """Zero-value RLE encoder

    Parameters:
        s (``bytes``):
            Bytes to encode

    Returns:
        ``bytes``: The encoded bytes
    """
    r: List[int] = []
    n: int = 0

    for b in s:
        if not b:
            n += 1
        else:
            if n:
                r.extend((0, n))
                n = 0

            r.append(b)

    if n:
        r.extend((0, n))

    return bytes(r)


def rle_decode(s: bytes) -> bytes:
    """Zero-value RLE decoder

    Parameters:
        s (``bytes``):
            Bytes to decode

    Returns:
        ``bytes``: The decoded bytes
    """
    r: List[int] = []
    z: bool = False

    for b in s:
        if not b:
            z = True
            continue

        if z:
            r.extend((0,) * b)
            z = False
        else:
            r.append(b)

    return bytes(r)
