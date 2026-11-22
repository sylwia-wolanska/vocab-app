from fastapi import APIRouter, status

from app.auth.dependencies import CurrentUser
from app.courses import service
from app.courses.schemas import CourseCreate, CourseRead
from app.db.session import DbSession

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, user: CurrentUser, db: DbSession) -> CourseRead:
    course = service.create_course(db, user.id, data)
    return CourseRead.model_validate(course)


@router.get("")
def list_courses(user: CurrentUser, db: DbSession) -> list[CourseRead]:
    return [
        CourseRead.model_validate(course)
        for course in service.list_courses(db, user.id)
    ]


@router.get("/{course_id}")
def get_course(course_id: int, user: CurrentUser, db: DbSession) -> CourseRead:
    course = service.get_course_for_user(db, user.id, course_id)
    return CourseRead.model_validate(course)
