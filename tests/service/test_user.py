from datetime import datetime

import jwt
import pytest
from pydantic import ValidationError

from src.core.config import settings
from src.core.security import decode_access_token, hash_password
from src.exception.user import (
    InvalidCredentialsException,
    UserAlreadyExistException,
    UserInactiveException,
)
from src.model.user import User, UserRole
from src.schema.request.user import LoginRequest, RegisterRequest

PASSWORD = "senha-forte-123"


def create_user(user_id: int = 1, email: str = "adm@sebraeprev.com.br", password: str = PASSWORD, role: str = UserRole.ADMIN, is_active: bool = True) -> User:
    user = User()
    user.id = user_id
    user.name = "Administrador"
    user.email = email
    user.password = hash_password(password)
    user.role = role
    user.is_active = is_active
    user.create_at = datetime.now()

    return user


class TestUserService:




    def test_login_with_success_returns_a_valid_token(self, user_service, user_repository_mock):

        user = create_user()
        user_repository_mock.find_by_email.return_value = user

        response = user_service.login(LoginRequest(email=user.email, password=PASSWORD))

        assert response.token_type == "bearer"

        payload = decode_access_token(response.access_token)
        assert payload["sub"] == "1"
        assert payload["email"] == user.email
        assert payload["role"] == UserRole.ADMIN

        user_repository_mock.find_by_email.assert_called_once_with(user.email)

    def test_login_normalizes_the_email_before_looking_it_up(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = create_user()

        user_service.login(LoginRequest(email="  ADM@Sebraeprev.com.br  ", password=PASSWORD))

        user_repository_mock.find_by_email.assert_called_once_with("adm@sebraeprev.com.br")

    def test_login_with_wrong_password_throws_exception(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = create_user()

        with pytest.raises(InvalidCredentialsException):
            user_service.login(LoginRequest(email="adm@sebraeprev.com.br", password="senha-errada"))

    def test_login_with_unknown_email_throws_the_same_exception_as_wrong_password(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = None

        with pytest.raises(InvalidCredentialsException):
            user_service.login(LoginRequest(email="ninguem@sebraeprev.com.br", password=PASSWORD))

    def test_login_with_inactive_user_throws_exception(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = create_user(is_active=False)

        with pytest.raises(UserInactiveException):
            user_service.login(LoginRequest(email="adm@sebraeprev.com.br", password=PASSWORD))

    def test_register_with_success(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = None
        user_repository_mock.save.side_effect = lambda user: setattr(user, "id", 2)

        request = RegisterRequest(name="  Kaua  ", email="  Kaua@Sebraeprev.com.br  ", password=PASSWORD)

        response = user_service.register(request)

        assert response.id == 2
        assert response.name == "Kaua"
        assert response.email == "kaua@sebraeprev.com.br"
        assert response.role == UserRole.USER
        assert response.is_active is True

        user_repository_mock.save.assert_called_once()

    def test_register_never_stores_the_plain_password(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = None
        user_repository_mock.save.side_effect = lambda user: setattr(user, "id", 2)

        user_service.register(RegisterRequest(name="Kaua", email="kaua@sebraeprev.com.br", password=PASSWORD))

        saved = user_repository_mock.save.call_args.args[0]

        assert saved.password != PASSWORD
        assert saved.password.startswith("$2b$")

    def test_register_with_existing_email_throws_exception(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = create_user()

        request = RegisterRequest(name="Kaua", email="adm@sebraeprev.com.br", password=PASSWORD)

        with pytest.raises(UserAlreadyExistException):
            user_service.register(request)


        user_repository_mock.save.assert_not_called()

    @pytest.mark.parametrize(
        "payload",
        [
            {"name": "", "email": "kaua@sebraeprev.com.br", "password": PASSWORD},
            {"name": "Kaua", "email": "invalido", "password": PASSWORD},
            {"name": "Kaua", "email": "kaua@sebraeprev.com.br", "password": "curta"},
            {"name": "Kaua", "email": "kaua@sebraeprev.com.br", "password": PASSWORD, "role": "ROOT"},
        ],
    )
    def test_register_request_rejects_invalid_payload(self, payload):
        with pytest.raises(ValidationError):
            RegisterRequest(**payload)

    def test_token_signed_with_another_secret_is_rejected(self, user_service, user_repository_mock):

        user_repository_mock.find_by_email.return_value = create_user()

        token = user_service.login(LoginRequest(email="adm@sebraeprev.com.br", password=PASSWORD)).access_token

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "outro-segredo-tambem-com-32-bytes-ou-mais", algorithms=[settings.JWT_ALGORITHM])
