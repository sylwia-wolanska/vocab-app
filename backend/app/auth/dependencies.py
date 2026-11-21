from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import DbSession
from app.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> User:
    subject = decode_access_token(token)
    user = db.get(User, int(subject)) if subject and subject.isdigit() else None
    if user is None or not user.is_active:
        raise UnauthorizedError("Could not validate credentials")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
