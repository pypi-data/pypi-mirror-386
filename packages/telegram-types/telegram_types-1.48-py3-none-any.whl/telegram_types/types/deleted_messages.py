from typing import List, Optional
from telegram_types.base import Base


class DeletedMessages(Base):
    # Если message_ids больше одного, значит, они были удалены одновременно.
    # Максимум 100
    message_ids: List[int]

    # Если chat_id нет, значит, это группа или личные сообщения.
    # Если есть, значит канал или супергруппа
    chat_id: Optional[int] = None

    @classmethod
    def from_telegram_type(cls, obj):
        if obj is None:
            return None
        return cls(**cls.from_telegram_type_dict(obj))

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        message_ids = []
        chat_id = None
        for m in obj:
            message_ids.append(m.id)
            if m.chat is not None:
                chat_id = m.chat.id
        return {'message_ids': message_ids, 'chat_id': chat_id}
