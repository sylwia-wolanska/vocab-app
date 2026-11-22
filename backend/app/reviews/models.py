from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReviewMode(StrEnum):
    LEARN = "learn"
    REVISE = "revise"


class Exercise(StrEnum):
    CHOOSE_WORD = "choose_word"
    CHOOSE_TRANSLATION = "choose_translation"
    TYPE_WORD = "type_word"


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("mode IN ('learn', 'revise')", name="mode"),
        CheckConstraint(
            "exercise IN ('choose_word', 'choose_translation', 'type_word')",
            name="exercise",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), index=True
    )
    mode: Mapped[str] = mapped_column(String(10))
    exercise: Mapped[str] = mapped_column(String(30))
    correct: Mapped[bool]
    answer: Mapped[str] = mapped_column(String(255))
    step_before: Mapped[int | None]
    step_after: Mapped[int | None]
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
