from fastapi import APIRouter, UploadFile

from app.auth.dependencies import CurrentUser
from app.core.exceptions import PayloadTooLargeError
from app.db.session import DbSession
from app.imports import service
from app.imports.schemas import ImportSummary

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/courses/{course_id}/import", tags=["imports"])


@router.post("")
def import_course_file(
    course_id: int,
    file: UploadFile,
    user: CurrentUser,
    db: DbSession,
    dry_run: bool = False,
) -> ImportSummary:
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeError("The file is larger than 5 MB")
    return service.import_file(db, user.id, course_id, content, dry_run=dry_run)
