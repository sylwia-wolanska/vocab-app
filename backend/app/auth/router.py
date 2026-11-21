from fastapi import APIRouter, status

from app.db.session import DbSession
from app.users import service as users_service
from app.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> UserRead:
    user = users_service.create_user(db, data.email, data.password)
    return UserRead.model_validate(user)
