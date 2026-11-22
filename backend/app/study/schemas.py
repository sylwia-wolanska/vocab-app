from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FlashCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    word: str
    translation: str
    description: str | None


class AnswerSubmit(BaseModel):
    answer: str = Field(max_length=255)


class AnswerResult(BaseModel):
    correct: bool
    card: FlashCard
    step: int
    due_at: datetime


class StudyCounts(BaseModel):
    due: int
    learn_new: int
    new_total: int
