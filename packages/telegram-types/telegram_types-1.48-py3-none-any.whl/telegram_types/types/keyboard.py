from typing import List, Optional

from telegram_types.base import Base


class InlineKeyboardButton(Base):
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None


class InlineKeyboardMarkup(Base):
    inline_keyboard: List[List[InlineKeyboardButton]]

    @classmethod
    def from_telegram_type_dict(cls, obj) -> Optional[dict]:
        cls_dict = super().from_telegram_type_dict(obj)
        if obj.inline_keyboard:
            cls_dict['inline_keyboard'] = [[
                InlineKeyboardButton.from_telegram_type(b) for b in row
            ] for row in obj.inline_keyboard]
            cls_dict['inline_keyboard'] = [[
                b for b in row if b
            ] for row in cls_dict['inline_keyboard']]
            cls_dict['inline_keyboard'] = [row for row in cls_dict['inline_keyboard'] if len(row)]
            if not len(cls_dict['inline_keyboard']):
                return None
        return cls_dict


class KeyboardButton(Base):
    text: str
    request_contact: Optional[bool] = None
    request_location: Optional[bool] = None

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        if isinstance(obj, str):
            return {'text': obj}
        else:
            return super().from_telegram_type_dict(obj)


class ReplyKeyboardMarkup(Base):
    keyboard: List[List[KeyboardButton]]
    resize_keyboard: Optional[bool] = None
    one_time_keyboard: Optional[bool] = None
    selective: Optional[bool] = None
    placeholder: Optional[str] = None

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = super().from_telegram_type_dict(obj)
        if obj.keyboard:
            cls_dict['keyboard'] = [[
                KeyboardButton.from_telegram_type(b) for b in row
            ] for row in obj.keyboard]
        return cls_dict


class ReplyKeyboardRemove(Base):
    selective: Optional[bool] = None


class ForceReply(Base):
    selective: Optional[bool] = None
    placeholder: Optional[str] = None


class ReplyMarkup(Base):
    inline: Optional[InlineKeyboardMarkup] = None
    reply: Optional[ReplyKeyboardMarkup] = None
    remove: Optional[ReplyKeyboardRemove] = None
    force_reply: Optional[ForceReply] = None

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = super().from_telegram_type_dict(obj)
        if hasattr(obj, 'inline_keyboard'):
            cls_dict['inline'] = InlineKeyboardMarkup.from_telegram_type(obj)
        elif hasattr(obj, 'keyboard'):
            cls_dict['reply'] = ReplyKeyboardMarkup.from_telegram_type(obj)
        else:
            cls_dict = None
        return cls_dict
