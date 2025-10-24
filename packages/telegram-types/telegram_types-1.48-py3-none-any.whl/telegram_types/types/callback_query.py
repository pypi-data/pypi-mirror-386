from typing import Optional

from telegram_types.types import User, Message
from telegram_types.base import Base


class CallbackQuery(Base):
    id: str
    from_user: User
    chat_instance: Optional[str] = None
    message: Optional[Message] = None
    inline_message_id: str
    data: Optional[str] = None
    game_short_name: Optional[str] = None
