from datetime import datetime

from sqlalchemy.orm import Session

from src.core.security import create_access_token, hash_password, verify_password
from src.exception.user import (
    InvalidCredentialsException,
    UserAlreadyExistException,
    UserInactiveException,
)
from src.model.user import User
from src.repository.user import UserRepository
from src.schema.request.user import LoginRequest, RegisterRequest
from src.schema.response.user import TokenResponse, UserResponse


class UserService:


    def __init__(self, user_repository: UserRepository, session: Session):
        self.user_repository = user_repository
        self.session = session




    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.user_repository.find_by_email(self._normalize_email(request.email))

        if user is None or not verify_password(request.password, user.password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise UserInactiveException()

        return TokenResponse(access_token=create_access_token(user.id, user.email, user.role))

    def register(self, request: RegisterRequest) -> UserResponse:
        email = self._normalize_email(request.email)

        if self.user_repository.find_by_email(email) is not None:
            raise UserAlreadyExistException()

        user = User()
        user.name = request.name.strip()
        user.email = email
        user.password = hash_password(request.password)
        user.role = request.role
        user.is_active = True
        user.create_at = datetime.now()

        self.user_repository.save(user)

        return UserResponse.model_validate(user)




    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()
