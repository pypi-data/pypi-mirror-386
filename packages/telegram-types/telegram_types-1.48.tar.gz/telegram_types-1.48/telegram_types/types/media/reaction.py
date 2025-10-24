from .base_media import BaseMedia


class Reaction(BaseMedia):
    emoji: str
    count: int
    chosen: bool
