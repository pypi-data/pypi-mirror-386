from telegram_types.base import Base


class BaseMedia(Base):
    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        result = super().from_telegram_type_dict(obj)
        if 'duration' in result:
            result['duration'] = int(result['duration'])
        return result
