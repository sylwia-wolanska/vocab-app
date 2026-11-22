from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.courses.models import Course
from app.courses.schemas import CourseCreate


def create_course(db: Session, user_id: int, data: CourseCreate) -> Course:
    course = Course(user_id=user_id, **data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"Course '{data.name}' already exists") from exc
    db.refresh(course)
    return course


def list_courses(db: Session, user_id: int) -> list[Course]:
    query = select(Course).where(Course.user_id == user_id).order_by(Course.name)
    return list(db.scalars(query))


def get_course_for_user(db: Session, user_id: int, course_id: int) -> Course:
    course = db.scalar(
        select(Course).where(Course.id == course_id, Course.user_id == user_id)
    )
    if course is None:
        raise NotFoundError(f"Course {course_id} not found")
    return course
