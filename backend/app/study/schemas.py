from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.reviews.models import Exercise


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


class LearnExercise(BaseModel):
    card_id: int
    exercise: Exercise
    prompt: str
    description: str | None
    options: list[str]
    answer: str


class LearnRound(BaseModel):
    cards: list[FlashCard]
    exercises: list[LearnExercise]


class LearnAnswerSubmit(BaseModel):
    exercise: Exercise
    answer: str = Field(max_length=255)


class LearnAnswerResult(BaseModel):
    correct: bool
    card: FlashCard
    learned: bool
    due_at: datetime | None
