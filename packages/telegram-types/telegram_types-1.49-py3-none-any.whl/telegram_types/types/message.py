from typing import List, Optional, Union, Dict

from telegram_types.types import User, Animation, Audio, Document, Photo, Video, Sticker, \
    Game, Voice, VideoNote, Contact, Location, Venue, WebPage, Poll, Dice, Reaction
from telegram_types.base import Base
from telegram_types.types.keyboard import ReplyMarkup
from telegram_types.media_attributes import MediaType


class ChatUpdate(Base):
    chat_id: int
    chat: Optional['Chat'] = None
    left: Optional[bool] = None
    unpinned_message_ids: Optional[list[int]] = None


class ServiceMessage(Base):
    id: int
    chat: 'Chat'
    outgoing: Optional[bool] = None
    from_user: Optional[User] = None
    sender_chat: Optional['Chat'] = None

    new_chat_members: Optional[List[User]] = None
    left_chat_member: Optional[User] = None
    new_chat_title: Optional[str] = None
    new_chat_photo: Optional[Photo] = None
    delete_chat_photo: Optional[bool] = None
    group_chat_created: Optional[bool] = None
    chat_created: Optional[bool] = None
    migrate_to_chat_id: Optional[int] = None
    migrate_from_chat_id: Optional[int] = None
    pinned_message: Optional['Message'] = None
    game_high_score: Optional[Dict] = None
    voice_chat_scheduled: Optional[Dict] = None
    voice_chat_started: Optional[Dict] = None
    voice_chat_ended: Optional[Dict] = None
    voice_chat_members_invited: Optional[Dict] = None


class Message(Base):
    id: int
    chat: 'Chat'
    outgoing: Optional[bool] = None
    date: Optional[int] = None
    edit_date: Optional[int] = None
    from_user: Optional[User] = None
    sender_chat: Optional['Chat'] = None
    views: Optional[int] = None
    via_bot: Optional[User] = None

    has_protected_content: Optional[bool] = None
    forward_from: Optional[User] = None
    forward_sender_name: Optional[str] = None
    forward_from_chat: Optional['Chat'] = None
    forward_from_message_id: Optional[int] = None
    forward_signature: Optional[str] = None
    forward_date: Optional[int] = None
    reply_to_message: Optional[Union['Message', ServiceMessage]] = None
    media_group_id: Optional[int] = None
    author_signature: Optional[str] = None
    reply_markup: Optional[ReplyMarkup] = None

    text: Optional[str] = None
    audio: Optional[Audio] = None
    document: Optional[Document] = None
    photo: Optional[Photo] = None
    sticker: Optional[Sticker] = None
    animation: Optional[Animation] = None
    game: Optional[Game] = None
    video: Optional[Video] = None
    voice: Optional[Voice] = None
    video_note: Optional[VideoNote] = None
    contact: Optional[Contact] = None
    location: Optional[Location] = None
    venue: Optional[Venue] = None
    web_page: Optional[Union[WebPage, bool]] = None
    poll: Optional[Poll] = None
    dice: Optional[Dice] = None
    has_media_spoiler: bool = False

    pinned_message: Optional['Message'] = None
    silent: bool = False

    @property
    def media(self) -> Optional[MediaType]:
        return (MediaType.ANIMATION if self.animation else MediaType.AUDIO if self.audio else
                MediaType.DOCUMENT if self.document else MediaType.PHOTO if self.photo else
                MediaType.VIDEO if self.video else MediaType.VIDEO_NOTE if self.video_note else
                MediaType.VOICE if self.voice else None)

    @property
    def service(self) -> bool:
        return bool(self.pinned_message)

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = super().from_telegram_type_dict(obj)
        cls_dict['text'] = obj.html_text
        if obj.reply_to_message:
            obj.reply_to_message.chat = obj.chat
            obj.reply_to_message.reply_to_message = None
            cls_dict['reply_to_message'] = cls.from_telegram_type(obj.reply_to_message)
        if obj.pinned_message:
            obj.pinned_message.chat = obj.chat
            cls_dict['reply_to_message'] = cls.from_telegram_type(obj.pinned_message)
        if obj.web_page:
            cls_dict['web_page'] = True
        if obj.reply_markup:
            cls_dict['reply_markup'] = ReplyMarkup.from_telegram_type(obj.reply_markup)
        cls_dict['has_media_spoiler'] = bool(obj.has_media_spoiler)
        cls_dict['silent'] = bool(obj.silent)
        return cls_dict


from telegram_types.types.chat import Chat

ServiceMessage.model_rebuild(force=True)
Message.model_rebuild(force=True)
