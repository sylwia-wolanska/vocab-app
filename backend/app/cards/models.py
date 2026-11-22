from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Card(TimestampMixin, Base):
    __tablename__ = "cards"
    __table_args__ = (UniqueConstraint("course_id", "excel_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    excel_id: Mapped[int]
    word: Mapped[str] = mapped_column(String(255))
    translation: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(server_default=true())

    learning_step: Mapped[int | None]
    recovery_target: Mapped[int | None]
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mistake_count: Mapped[int] = mapped_column(server_default=text("0"))
