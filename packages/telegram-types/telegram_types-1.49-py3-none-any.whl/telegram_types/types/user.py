from typing import Optional, List

from telegram_types.types import Restriction, ChatPhoto
from telegram_types.base import Base

from telegram_types.enums import UserStatus as Status


class User(Base):
    id: int
    is_self: Optional[bool] = None
    is_contact: Optional[bool] = None
    is_mutual_contact: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_bot: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_restricted: Optional[bool] = None
    is_scam: Optional[bool] = None
    is_fake: Optional[bool] = None
    is_support: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[Status] = None
    last_online_date: Optional[int] = None
    next_offline_date: Optional[int] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    dc_id: Optional[int] = None
    phone_number: Optional[str] = None
    photo: Optional[ChatPhoto] = None
    restrictions: Optional[List[Restriction]] = None
