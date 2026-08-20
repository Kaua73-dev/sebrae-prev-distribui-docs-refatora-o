
import pytest
from pydantic import ValidationError

from src.exception.prefix.prefix_exception import PrefixRequiredException
from src.model.prefix import Prefix
from src.schema.request.user_email import UserEmailRequest
from tests.conftest import user_email_service


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



