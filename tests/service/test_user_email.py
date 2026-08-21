from datetime import datetime

import pytest
from pydantic import ValidationError

from src.model.user_email import UserEmail
from src.exception.prefix.prefix_exception import PrefixNotFoundException, PrefixRequiredException
from src.exception.user_email import UserEmailAlreadyException, UserEmailNotFoundException
from src.model.prefix import Prefix
from src.schema.request.user_email import UserEmailRequest, UserEmailUpdateRequest


class TestUserEmailService:




    def test_create_user_email_with_success(self, user_email_repository_mock, user_email_service, prefix_repository_mock):

        existing_prefix = Prefix()
        existing_prefix.prefix_name = "BSB"

        def fake_save(user_email):
            user_email.id = 1

        request = UserEmailRequest(user_email_name="teste@gmail.com", prefix_name="BSB")

        prefix_repository_mock.find_by_prefix_name.return_value = existing_prefix
        user_email_repository_mock.find_by_email.return_value = None
        user_email_repository_mock.save.side_effect = fake_save


        response = user_email_service.create_user_email(request)

        assert response.user_email_name == "teste@gmail.com"
        assert response.is_active is True
        assert response.prefix_name == "BSB"
        assert response.id == 1


        prefix_repository_mock.find_by_prefix_name.assert_called_once_with("BSB")
        user_email_repository_mock.find_by_email.assert_called_once_with("teste@gmail.com")
        user_email_repository_mock.save.assert_called_once()

    def test_create_user_email_with_empty_prefix_name_throws_exception(self, user_email_repository_mock,  user_email_service, prefix_repository_mock):
        request = UserEmailRequest(user_email_name='teste@gmail.com', prefix_name="")

        with pytest.raises(PrefixRequiredException):
            user_email_service.create_user_email(request)

    @pytest.mark.parametrize("user_email_name", [None, ""])
    def test_create_user_email_with_invalid_email_address(self, user_email_name):
        with pytest.raises(ValidationError):
            UserEmailRequest(user_email_name=user_email_name, prefix_name="BSB")

    @pytest.mark.parametrize("prefix_name", [None])
    def test_create_user_email_with_invalid_prefix_name(self, prefix_name):
        with pytest.raises(ValidationError):
            UserEmailRequest(user_email_name="teste@gmail.com", prefix_name=prefix_name)

    def test_create_user_email_with_prefix_not_found_throws_exception(self, user_email_repository_mock, user_email_service, prefix_repository_mock):

        request = UserEmailRequest(user_email_name="teste@gmail.com", prefix_name="XPTO")
        prefix_repository_mock.find_by_prefix_name.return_value = None

        with pytest.raises(PrefixNotFoundException):
            user_email_service.create_user_email(request)


        user_email_repository_mock.save.assert_not_called()

    def test_create_user_email_already_exists_throws_exception(self, user_email_repository_mock, user_email_service, prefix_repository_mock):

        existing_prefix = Prefix()
        existing_prefix.prefix_name = "BSB"

        request = UserEmailRequest(user_email_name="teste@gmail.com", prefix_name="BSB")
        prefix_repository_mock.find_by_prefix_name.return_value = existing_prefix
        user_email_repository_mock.find_by_email.return_value = object()

        with pytest.raises(UserEmailAlreadyException):
            user_email_service.create_user_email(request)


        user_email_repository_mock.save.assert_not_called()

    def test_find_all_user_email_with_prefix_success(self, user_email_repository_mock, user_email_service, prefix_repository_mock):

        prefix = Prefix()
        prefix.id = 1
        prefix.prefix_name = "GMAIL"

        user_email = UserEmail()
        user_email.id = 1
        user_email.email = "teste@gmail.com"
        user_email.is_active = True
        user_email.create_at = datetime.now()
        user_email.prefix_id = 1
        user_email.prefix = prefix

        user_email_repository_mock.find_all_with_prefix.return_value = [user_email]

        response = user_email_service.find_user_emails()

        user_email_repository_mock.find_all_with_prefix.assert_called_once()
        assert len(response) == 1
        assert response[0].id == user_email.id
        assert response[0].user_email_name == user_email.email
        assert response[0].is_active == user_email.is_active
        assert response[0].prefix_name == "GMAIL"

    def test_find_all_user_email_returns_empty_list(self, user_email_repository_mock, user_email_service):
        user_email_repository_mock.find_all_with_prefix.return_value = []

        response = user_email_service.find_user_emails()

        assert response == []
        user_email_repository_mock.find_all_with_prefix.assert_called_once()

    def test_update_user_email_with_success(self, user_email_repository_mock, user_email_service, prefix_repository_mock):

        new_prefix = Prefix()
        new_prefix.id = 2
        new_prefix.prefix_name = "SP"

        existing_user_email = UserEmail()
        existing_user_email.id = 1
        existing_user_email.email = "antigo@gmail.com"
        existing_user_email.is_active = True
        existing_user_email.create_at = datetime.now()

        request = UserEmailUpdateRequest(id=1, user_email_name="novo@gmail.com", prefix_name="SP", is_active=False)

        user_email_repository_mock.find_by_id.return_value = existing_user_email
        user_email_repository_mock.find_by_email.return_value = None
        prefix_repository_mock.find_by_prefix_name.return_value = new_prefix

        response = user_email_service.update_user_email(request)

        assert response.user_email_name == "novo@gmail.com"
        assert response.prefix_name == "SP"
        assert response.is_active is False

        assert existing_user_email.email == "novo@gmail.com"
        assert existing_user_email.prefix is new_prefix

        user_email_repository_mock.find_by_id.assert_called_once_with(1)
        prefix_repository_mock.find_by_prefix_name.assert_called_once_with("SP")
        user_email_repository_mock.save.assert_called_once_with(existing_user_email)

    def test_update_user_email_not_found_throws_exception(self, user_email_repository_mock, user_email_service):

        request = UserEmailUpdateRequest(id=99, user_email_name="teste@gmail.com", prefix_name="BSB", is_active=True)
        user_email_repository_mock.find_by_id.return_value = None

        with pytest.raises(UserEmailNotFoundException):
            user_email_service.update_user_email(request)


        user_email_repository_mock.save.assert_not_called()
        
    def test_delete_user_email_with_success(self, user_email_repository_mock, user_email_service):

        existing_user_email = object()
        user_email_repository_mock.find_by_id.return_value = existing_user_email

        user_email_service.delete_user_email(1)

        user_email_repository_mock.find_by_id.assert_called_once_with(1)
        user_email_repository_mock.delete.assert_called_once_with(existing_user_email)

    def test_delete_user_email_not_found_throws_exception(self, user_email_repository_mock, user_email_service):

        user_email_repository_mock.find_by_id.return_value = None

        with pytest.raises(UserEmailNotFoundException):
            user_email_service.delete_user_email(99)


        user_email_repository_mock.delete.assert_not_called()
