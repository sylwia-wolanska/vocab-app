from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.core.clock import Now
from app.db.session import DbSession
from app.study import service
from app.study.schemas import StudyCounts

router = APIRouter(prefix="/courses/{course_id}/study", tags=["study"])


@router.get("")
def get_study_counts(
    course_id: int, user: CurrentUser, db: DbSession, now: Now
) -> StudyCounts:
    return service.get_counts(db, user.id, course_id, now)
