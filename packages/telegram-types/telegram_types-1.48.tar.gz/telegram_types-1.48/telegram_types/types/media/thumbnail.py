from .base_media import BaseMedia


class Thumbnail(BaseMedia):
    owner_id: int
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: int
