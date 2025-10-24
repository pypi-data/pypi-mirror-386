from typing import Optional

from pydantic import BaseModel
from telegram_types.enums.message_media_type import MessageMediaType as MediaType
from telegram_types.enums.poll_type import PollType


class AnimationAttributes(BaseModel):
    thumb: Optional[str] = None
    duration: Optional[int] = 0
    width: Optional[int] = 0
    height: Optional[int] = 0
    file_name: Optional[str] = None
    unsave: Optional[bool] = False
    has_spoiler: Optional[bool] = False


class AudioAttributes(BaseModel):
    thumb: Optional[str] = None
    duration: Optional[int] = 0
    title: Optional[str] = None
    performer: Optional[str] = None
    file_name: Optional[str] = None


class DocumentAttributes(BaseModel):
    thumb: Optional[str] = None
    file_name: Optional[str] = None
    force_document: Optional[bool] = None


class PhotoAttributes(BaseModel):
    has_spoiler: Optional[bool] = False


class VideoAttributes(BaseModel):
    thumb: Optional[str] = None
    duration: Optional[int] = 0
    width: Optional[int] = 0
    height: Optional[int] = 0
    file_name: Optional[str] = None
    supports_streaming: Optional[bool] = True
    has_spoiler: Optional[bool] = False


class VideoNoteAttributes(BaseModel):
    thumb: Optional[str] = None
    duration: Optional[int] = 0
    length: Optional[int] = 1


class VoiceAttributes(BaseModel):
    duration: Optional[int] = 0
