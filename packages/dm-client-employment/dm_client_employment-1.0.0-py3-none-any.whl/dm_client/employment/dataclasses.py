from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class Classify:
    id: Optional[str] = None
    title: str = ""
    location: str = ""
    category: str = ""
    sub_category: str = ""
    work_arrangement: str = ""
    work_type: str = ""
    pay_type: str = ""
    pay_currency: str = ""
    pay: float = 0.0
    show_salary: bool = False


@dataclass
class Details:
    summary: str = ""
    description: str = ""
    requirement: str = ""
    video_link: str = ""


@dataclass
class Choice:
    option: str


@dataclass
class Question:
    question_type: str
    question: Optional[str] = None
    max_length: Optional[int] = None
    max_answers: Optional[int] = None
    choices: Optional[List[Choice]] = None


@dataclass
class Advertise:
    billing_plan: str
    duration: int = 0


@dataclass
class JobPostingDC:
    classify: Classify
    details: Details
    questions: List[Question]
    advertise: Advertise

    def to_dict(self) -> dict:
        return self._filter_none(asdict(self))

    @staticmethod
    def _filter_none(data: dict) -> dict:
        """Recursively remove keys with None values."""
        if isinstance(data, dict):
            return {k: JobPostingDC._filter_none(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [JobPostingDC._filter_none(v) for v in data]
        else:
            return data

    @classmethod
    def from_dict(cls, data: dict) -> 'JobPostingDC':
        return cls(
            classify=Classify(**data['classify']),
            details=Details(**data['details']),
            questions=[
                Question(
                    question_type=q['question_type'],
                    question=q.get('question'),
                    max_length=q.get('max_length'),
                    max_answers=q.get('max_answers'),
                    choices=[
                        Choice(**choice) for choice in q.get('choices', [])
                    ] if 'choices' in q else None
                ) for q in data['questions']
            ],
            advertise=Advertise(
                billing_plan=data['advertise']['billing_plan']
            )
        )

    def __str__(self) -> str:
        return json.dumps(asdict(self), indent=2)


