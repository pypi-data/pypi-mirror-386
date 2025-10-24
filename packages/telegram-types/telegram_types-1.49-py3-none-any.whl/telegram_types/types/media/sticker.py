from typing import List, Optional

from .thumbnail import Thumbnail
from .base_media import BaseMedia


class Sticker(BaseMedia):
    owner_id: int
    file_id: str
    file_unique_id: str
    width: int
    height: int
    is_animated: bool
    is_video: bool
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    date: Optional[int] = None
    emoji: Optional[str] = None
    set_name: Optional[str] = None
    thumbs: Optional[List[Thumbnail]] = None
