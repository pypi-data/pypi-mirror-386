import inspect
import datetime
from base64 import b64encode
from enum import Enum
import typing

from pydantic import BaseModel, ConfigDict

from telegram_types.utils import datetime_to_timestamp


def is_generic(t: type):
    return hasattr(t, "__origin__")


def is_generic_of(t: object, origin: object) -> bool:
    # Example: is_generic_of(List[str], list) == True
    return is_generic(t) and t.__origin__ == origin  # type: ignore


def is_union(t: object):
    return is_generic_of(t, typing.Union)


def is_optional(t: object) -> bool:
    return is_union(t) and len(t.__args__) == 2 and t.__args__[1] == type(None)  # type: ignore


class Base(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    @classmethod
    def convert_to_pydantic(cls, obj, field_type: 'Base' = None):
        if field_type and is_optional(field_type):
            field_type = field_type.__args__[0]
        if obj is None:
            return None
        if isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, bytes):
            return b64encode(obj).decode()
        if isinstance(obj, datetime.datetime):
            return datetime_to_timestamp(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, list):
            sub_field_type = (field_type.__args__[0]
                              if field_type and is_generic(field_type) and len(field_type.__args__)
                              else None)
            return [cls.convert_to_pydantic(o, field_type=sub_field_type) for o in obj]
        if field_type is not None:
            if inspect.isclass(field_type) and issubclass(field_type, Base):
                return field_type.from_telegram_type(obj)
        return obj

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = {}
        if 'owner_id' in cls.model_fields:
            cls_dict['owner_id'] = obj._client.me.id
        keys = obj.__dict__.keys() if hasattr(obj, '__dict__') else obj.__slots__
        for a in keys:
            v = getattr(obj, a, None)
            if a not in cls.model_fields:
                continue
            field_type = cls.model_fields[a].annotation
            cls_dict[a] = cls.convert_to_pydantic(v, field_type=field_type)
            if a == 'available_reactions':
                print('a', field_type, repr(cls_dict[a]))
        return cls_dict

    @classmethod
    def from_telegram_type(cls, obj):
        if obj is None:
            return None
        if isinstance(obj, list):
            return [cls.from_telegram_type(o) for o in obj]
        telegram_type_dict = cls.from_telegram_type_dict(obj)
        if telegram_type_dict is None:
            return None
        return cls(**telegram_type_dict)
