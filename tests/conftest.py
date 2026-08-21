from unittest.mock import Mock, MagicMock

import pytest

from src.service.user_email import UserEmailService
from src.service.prefix.prefix_service import PrefixService
from src.service.preparation.preparation_service import PreparationService



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


# O PreparationService recebe o PrefixService inteiro (nao o repositorio), entao aqui
# o mock e do proprio service — quem manda no teste e o find_prefix_required_true().
@pytest.fixture
def prefix_service_mock():
    return Mock()


@pytest.fixture
def preparation_service(prefix_service_mock: Mock, user_email_repository_mock: Mock):
    return PreparationService(prefix_service=prefix_service_mock, user_email_repository=user_email_repository_mock)