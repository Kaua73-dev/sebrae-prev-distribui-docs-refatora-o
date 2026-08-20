from unittest.mock import Mock, MagicMock

import pytest

from src.service.user_email import UserEmailService
from src.service.prefix.prefix_service import PrefixService



@pytest.fixture
def session_mock():
    return MagicMock()



@pytest.fixture
def prefix_repository_mock():
    return Mock()

@pytest.fixture
def prefix_service(prefix_repository_mock: Mock, session_mock: Mock):
    return PrefixService(prefix_repository=prefix_repository_mock, session=session_mock)

@pytest.fixture
def user_email_repository_mock():
    return Mock()


@pytest.fixture
def user_email_service(user_email_repository_mock: Mock,prefix_repository_mock: Mock,session_mock: MagicMock):
    return UserEmailService(user_email_repository=user_email_repository_mock,prefix_repository=prefix_repository_mock,session=session_mock)