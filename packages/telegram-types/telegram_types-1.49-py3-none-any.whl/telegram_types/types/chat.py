from typing import List, Optional

from telegram_types.types import Restriction, ChatPhoto
from telegram_types.base import Base
from telegram_types.enums.chat_type import ChatType


class ChatPermissions(Base):
    can_send_messages: Optional[bool] = None
    can_send_media_messages: Optional[bool] = None
    can_send_other_messages: Optional[bool] = None
    can_send_polls: Optional[bool] = None
    can_add_web_page_previews: Optional[bool] = None
    can_change_info: Optional[bool] = None
    can_invite_users: Optional[bool] = None
    can_pin_messages: Optional[bool] = None


class Chat(Base):
    id: int
    type: ChatType
    is_verified: Optional[bool] = None
    is_restricted: Optional[bool] = None
    is_creator: Optional[bool] = None
    is_scam: Optional[bool] = None
    is_fake: Optional[bool] = None
    is_support: Optional[bool] = None
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    photo: Optional[ChatPhoto] = None
    bio: Optional[str] = None
    description: Optional[str] = None
    dc_id: Optional[int] = None
    has_protected_content: Optional[bool] = None
    invite_link: Optional[str] = None
    pinned_message: Optional['Message'] = None
    sticker_set_name: Optional[str] = None
    can_set_sticker_set: Optional[bool] = None
    members_count: Optional[int] = None
    restrictions: Optional[List[Restriction]] = None
    permissions: Optional[ChatPermissions] = None
    distance: Optional[int] = None
    linked_chat: Optional['Chat'] = None
    send_as_chat: Optional['Chat'] = None

    @property
    def name(self) -> str:
        if self.title:
            return self.title
        else:
            name = self.first_name
            if self.last_name:
                name += ' ' + self.last_name
            return name


from telegram_types.types.message import Message

Chat.model_rebuild(force=True)
