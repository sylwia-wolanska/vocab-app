from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends


def utc_now() -> datetime:
    return datetime.now(UTC)


Now = Annotated[datetime, Depends(utc_now)]
