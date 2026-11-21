from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    excel_id: int
    word: str
    translation: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CardPage(BaseModel):
    items: list[CardRead]
    total: int
    limit: int
    offset: int
