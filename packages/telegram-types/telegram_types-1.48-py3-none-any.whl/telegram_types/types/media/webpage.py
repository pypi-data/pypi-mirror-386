from typing import Optional

from . import Audio, Document, Photo, Animation, Video
from .base_media import BaseMedia


class WebPage(BaseMedia):
    id: str
    url: str
    display_url: str
    type: Optional[str] = None
    site_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    audio: Optional[Audio] = None
    document: Optional[Document] = None
    Photo: Optional[Photo] = None
    animation: Optional[Animation] = None
    video: Optional[Video] = None
    embed_url: Optional[str] = None
    embed_type: Optional[str] = None
    embed_width: Optional[int] = None
    embed_height: Optional[int] = None
    duration: Optional[int] = None
    author: Optional[str] = None
