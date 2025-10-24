from typing import Optional

from .location import Location
from .base_media import BaseMedia


class Venue(BaseMedia):
    location: Location
    title: str
    address: str
    foursquare_id: Optional[str] = None
    foursquare_type: Optional[str] = None
