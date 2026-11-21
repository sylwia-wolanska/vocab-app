from fastapi import APIRouter, UploadFile

from app.core.exceptions import PayloadTooLargeError
from app.db.session import DbSession
from app.imports import service
from app.imports.schemas import ImportSummary

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/courses/{course_id}/import", tags=["imports"])


@router.post("")
def import_course_file(
    course_id: int, file: UploadFile, db: DbSession
) -> ImportSummary:
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeError("The file is larger than 5 MB")
    return service.import_file(db, course_id, content)
