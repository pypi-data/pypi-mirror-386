from typing import Optional

from .base_media import BaseMedia


class Voice(BaseMedia):
    owner_id: int
    file_id: str
    file_unique_id: str
    duration: int
    waveform: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    date: Optional[int] = None
