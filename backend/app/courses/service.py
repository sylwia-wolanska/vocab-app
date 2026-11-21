from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.courses.models import Course
from app.courses.schemas import CourseCreate


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f"Course '{data.name}' already exists") from exc
    db.refresh(course)
    return course


def list_courses(db: Session) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.name)))


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError(f"Course {course_id} not found")
    return course
