from datetime import datetime

from sqlalchemy.orm import Session

from src.exception.prefix.prefix_exception import PrefixNotFoundException, PrefixRequiredException
from src.exception.UserEmail.user_email_exception import (
    UserEmailAlreadyException,
    UserEmailNotFoundException,
    UserEmailRequiredException,
)
from src.model.prefix import Prefix
from src.model.user_email import UserEmail
from src.repository.prefix import PrefixRepository
from src.repository.user_email import UserEmailRepository
from src.schema.request.user_email import UserEmailRequest, UserEmailUpdateRequest
from src.schema.response.user_email import UserEmailResponse


class UserEmailService:


    def __init__(self, user_email_repository: UserEmailRepository, prefix_repository: PrefixRepository, session: Session):
        self.user_email_repository = user_email_repository
        self.prefix_repository = prefix_repository
        self.session = session

    @staticmethod
    def _normalize_email(email: str) -> str:
        if email is None or email.strip() == "":
            raise UserEmailRequiredException()

        return email.strip().lower()

    def _find_prefix(self, prefix_name: str) -> Prefix:
        if prefix_name is None or prefix_name.strip() == "":
            raise PrefixRequiredException()

        prefix = self.prefix_repository.find_by_prefix_name(prefix_name.strip().upper())

        if prefix is None:
            raise PrefixNotFoundException()

        return prefix

    @staticmethod
    def _to_response(user_email: UserEmail) -> UserEmailResponse:
        return UserEmailResponse(
            id=user_email.id,
            user_email_name=user_email.email,
            is_active=user_email.is_active,
            created_at=user_email.create_at,
            prefix_name=user_email.prefix.prefix_name,
        )


    def create_user_email(self, request: UserEmailRequest) -> UserEmailResponse:

        email = self._normalize_email(request.user_email_name)
        prefix = self._find_prefix(request.prefix_name)

        if self.user_email_repository.find_by_email(email) is not None:
            raise UserEmailAlreadyException()

        user_email = UserEmail()
        user_email.email = email
        user_email.is_active = True
        user_email.create_at = datetime.now()
        user_email.prefix = prefix

        self.user_email_repository.save(user_email)

        return self._to_response(user_email)

    def find_user_emails(self) -> list[UserEmailResponse]:
        return list(map(self._to_response, self.user_email_repository.find_all_with_prefix()))

    def update_user_email(self, request: UserEmailUpdateRequest) -> UserEmailResponse:

        user_email = self.user_email_repository.find_by_id(request.id)

        if user_email is None:
            raise UserEmailNotFoundException()

        email = self._normalize_email(request.user_email_name)

        if request.prefix_name is None or request.prefix_name.strip() == "":
            prefix = user_email.prefix
        else:
            prefix = self._find_prefix(request.prefix_name)

        owner_of_email = self.user_email_repository.find_by_email(email)

        if owner_of_email is not None and owner_of_email.id != user_email.id:
            raise UserEmailAlreadyException()

        user_email.email = email
        user_email.is_active = request.is_active
        user_email.prefix = prefix

        self.user_email_repository.save(user_email)

        return self._to_response(user_email)

    def delete_user_email(self, user_email_id: int) -> None:

        user_email = self.user_email_repository.find_by_id(user_email_id)

        if user_email is None:
            raise UserEmailNotFoundException()

        self.user_email_repository.delete(user_email)
