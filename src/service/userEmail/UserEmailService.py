from datetime import datetime

from sqlalchemy.orm import Session

from exception.prefix import PrefixNotFoundException
from exception.prefix.prefix_exception import PrefixRequiredException
from repository.user_email.user_email_repository import UserEmailRepository
from schema.request.user_email.User_email_request import UserEmailRequest
from schema.response.user_email.User_email_response import UserEmailResponse
from src.exception.UserEmail.user_email_exception import *
from src.model.user_email.User_email import UserEmail
from src.repository.prefix.prefix_repository import *


class UserEmailService:


    def __init__(self, email_repository: UserEmailRepository, session: Session, prefx_repository: PrefixRepository):
        self.user_email_repository = email_repository
        self.session = session
        self.prefix_repository = prefx_repository


    @staticmethod
    def _to_response(userEmail: UserEmail) -> UserEmailResponse:
        return UserEmailResponse.model_validate(userEmail)


    def create_user_email(self, request: UserEmailRequest) -> UserEmailResponse:

        if request.user_email_name is None or request.user_email_name == "":
            raise UserEmailRequiredException()

        if self.user_email_repository.find_by_email(request.user_email_name) is None:
            raise UserEmailNotFoundException()

        with self.session.begin():
            prefix = self.prefix_repository.find_by_prefix_name(request.prefix_name)
            if prefix is None:
                raise PrefixNotFoundException(request.prefix_name)


        use_email = UserEmail()
        use_email.email = request.user_email_name
        use_email.isActive = True
        use_email.create_at = datetime.now()
        use_email.prefix = prefix

        self.session.add(use_email)
        return self._to_response(use_email)


