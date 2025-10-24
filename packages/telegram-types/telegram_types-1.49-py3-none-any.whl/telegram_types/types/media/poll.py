from typing import List, Optional

from .base_media import BaseMedia

from telegram_types.enums.poll_type import PollType


class PollOption(BaseMedia):
    text: str
    voter_count: int
    data: str

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = super().from_telegram_type_dict(obj)
        if not isinstance(obj.text, str) and hasattr(obj.text, 'text'):
            cls_dict['text'] = obj.text.text
        return cls_dict


class Poll(BaseMedia):
    id: str
    question: str
    options: List[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: Optional[bool] = None
    type: Optional[PollType] = None
    allows_multiple_answers: Optional[bool] = None
    chosen_option: Optional[int] = None

    @classmethod
    def from_telegram_type_dict(cls, obj) -> dict:
        cls_dict = super().from_telegram_type_dict(obj)
        if not isinstance(obj.question, str) and hasattr(obj.question, 'text'):
            cls_dict['question'] = obj.question.text
        return cls_dict
