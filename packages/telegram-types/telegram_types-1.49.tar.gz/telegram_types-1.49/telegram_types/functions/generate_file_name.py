from mimetypes import MimeTypes
import struct
from enum import IntEnum
from io import BytesIO
from datetime import datetime

from telegram_types.types import Message
from telegram_types.utils import rle_decode, b64_decode, randstr, timestamp_to_datetime


def generate_file_name(message):
    mimetypes = MimeTypes()
    available_media = ("audio", "document", "photo", "sticker", "animation", "video", "voice",
                       "video_note", "new_chat_photo")

    if isinstance(message, Message):
        for kind in available_media:
            media = getattr(message, kind, None)

            if media is not None:
                break
        else:
            raise ValueError("This message doesn't contain any downloadable media")
    else:
        media = message

    if isinstance(media, str):
        file_id_str = media
    else:
        file_id_str = media.file_id

    file_type = get_file_id_type(file_id_str)

    media_file_name = getattr(media, "file_name", "")
    mime_type = getattr(media, "mime_type", "")
    date = getattr(media, "date", None)

    file_name = media_file_name or ""

    if not file_name:
        guessed_extension = mimetypes.guess_extension(mime_type)

        if file_type in PHOTO_TYPES:
            extension = ".jpg"
        elif file_type == FileType.VOICE:
            extension = guessed_extension or ".ogg"
        elif file_type in (FileType.VIDEO, FileType.ANIMATION, FileType.VIDEO_NOTE):
            extension = guessed_extension or ".mp4"
        elif file_type == FileType.DOCUMENT:
            extension = guessed_extension or ".zip"
        elif file_type == FileType.STICKER:
            extension = guessed_extension or ".webp"
        elif file_type == FileType.AUDIO:
            extension = guessed_extension or ".mp3"
        else:
            extension = ".unknown"

        file_name = "{}_{}_{}{}".format(
            FileType(file_type).name.lower(),
            (timestamp_to_datetime(date) or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S"),
            randstr(),
            extension
        )
    return file_name


class FileType(IntEnum):
    """Known file types"""
    THUMBNAIL = 0
    CHAT_PHOTO = 1  # ProfilePhoto
    PHOTO = 2
    VOICE = 3  # VoiceNote
    VIDEO = 4
    DOCUMENT = 5
    ENCRYPTED = 6
    TEMP = 7
    STICKER = 8
    AUDIO = 9
    ANIMATION = 10
    ENCRYPTED_THUMBNAIL = 11
    WALLPAPER = 12
    VIDEO_NOTE = 13
    SECURE_RAW = 14
    SECURE = 15
    BACKGROUND = 16
    DOCUMENT_AS_FILE = 17


PHOTO_TYPES = {FileType.THUMBNAIL, FileType.CHAT_PHOTO, FileType.PHOTO, FileType.WALLPAPER,
               FileType.ENCRYPTED_THUMBNAIL}
DOCUMENT_TYPES = set(FileType) - PHOTO_TYPES


WEB_LOCATION_FLAG = 1 << 24
FILE_REFERENCE_FLAG = 1 << 25


def get_file_id_type(file_id: str):
    decoded = rle_decode(b64_decode(file_id))

    # region read version
    # File id versioning. Major versions lower than 4 don't have a minor version
    major = decoded[-1]

    if major < 4:
        buffer = BytesIO(decoded[:-1])
    else:
        buffer = BytesIO(decoded[:-2])
    # endregion

    file_type, dc_id = struct.unpack("<ii", buffer.read(8))

    # Remove flags to restore the actual type id value
    file_type &= ~WEB_LOCATION_FLAG
    file_type &= ~FILE_REFERENCE_FLAG
    # endregion

    try:
        return FileType(file_type)
    except ValueError:
        raise ValueError(f"Unknown file_type {file_type} of file_id {file_id}")
