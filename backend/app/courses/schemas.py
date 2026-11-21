from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    source_language: str = Field(min_length=2, max_length=10)
    target_language: str = Field(min_length=2, max_length=10)


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_language: str
    target_language: str
    created_at: datetime
    updated_at: datetime
