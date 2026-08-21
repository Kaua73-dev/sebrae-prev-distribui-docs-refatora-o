import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm.session import Session

from src.core.database import get_db
from src.core.security import decode_access_token
from src.exception.user import (
    NotAuthenticatedException,
    NotEnoughPermissionException,
    UserInactiveException,
)
from src.model.user import User
from src.repository.dispatch import DispatchRepository
from src.repository.prefix import PrefixRepository
from src.repository.user import UserRepository
from src.repository.user_email import UserEmailRepository
from src.service.dispatch import DispatchService
from src.service.prefix.prefix_service import PrefixService
from src.service.preparation.preparation_service import PreparationService
from src.service.user import UserService
from src.service.user_email import UserEmailService

# auto_error=False para o 401 sair pelos exception handlers do projeto, com o mesmo
# formato {"detail": ...} das outras rotas, em vez do HTTPException cru do FastAPI.
bearer_scheme = HTTPBearer(auto_error=False)


def get_prefix_service(db: Session = Depends(get_db)) -> PrefixService:
    return PrefixService(PrefixRepository(db), db)

def get_user_email_service(db: Session = Depends(get_db)) -> UserEmailService:
    return UserEmailService(UserEmailRepository(db), PrefixRepository(db), db)

def get_preparation_service(
    prefix_service: PrefixService = Depends(get_prefix_service),
    db: Session = Depends(get_db),
) -> PreparationService:
    return PreparationService(prefix_service, UserEmailRepository(db))

def get_dispatch_service(
    preparation_service: PreparationService = Depends(get_preparation_service),
    db: Session = Depends(get_db),
) -> DispatchService:
    return DispatchService(DispatchRepository(db), preparation_service, db)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db), db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise NotAuthenticatedException()

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise NotAuthenticatedException()

    user = UserRepository(db).find_by_id(int(payload["sub"]))

    if user is None:
        raise NotAuthenticatedException()

    if not user.is_active:
        raise UserInactiveException()

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise NotEnoughPermissionException()

    return current_user
