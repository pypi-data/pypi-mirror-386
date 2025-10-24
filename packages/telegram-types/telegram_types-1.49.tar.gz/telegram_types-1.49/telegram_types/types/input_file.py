from typing import Optional

from telegram_types.base import Base


class InputFile(Base):
    id: int
    parts: int
    name: str
    md5_checksum: Optional[str] = None
