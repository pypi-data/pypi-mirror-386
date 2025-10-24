from typing import List, Optional

from .thumbnail import Thumbnail
from .base_media import BaseMedia


class Photo(BaseMedia):
    owner_id: int
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int
    date: int
    ttl_seconds: Optional[int] = None
    thumbs: Optional[List[Thumbnail]] = None
