from typing import Optional

from . import Photo, Animation
from .base_media import BaseMedia


class Game(BaseMedia):
    id: int
    title: str
    short_name: str
    description: str
    photo: Photo
    thumbs: Optional[Animation] = None
