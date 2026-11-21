from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import CurrentUser
from app.auth.schemas import Token
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token
from app.db.session import DbSession
from app.users import service as users_service
from app.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession) -> UserRead:
    user = users_service.create_user(db, data.email, data.password)
    return UserRead.model_validate(user)


@router.post("/token")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> Token:
    user = users_service.authenticate(db, form.username, form.password)
    if user is None:
        raise UnauthorizedError("Incorrect email or password")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me")
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
