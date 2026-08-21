from unittest.mock import AsyncMock, Mock, MagicMock

import pytest

from src.service.dispatch.dispatch_service import DispatchService
from src.service.user import UserService
from src.service.mail import MailService
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


# AsyncMock porque o send_message do FastMail e await. Com Mock comum o teste
# quebraria em "coroutine expected" antes de chegar em qualquer assert.
@pytest.fixture
def mail_mock():
    return AsyncMock()


@pytest.fixture
def mail_service(mail_mock: AsyncMock):
    return MailService(mail=mail_mock)


@pytest.fixture
def dispatch_repository_mock():
    return Mock()


@pytest.fixture
def preparation_service_mock():
    return Mock()


@pytest.fixture
def dispatch_service(dispatch_repository_mock: Mock, preparation_service_mock: Mock, session_mock: MagicMock):
    return DispatchService(dispatch_repository=dispatch_repository_mock, preparation_service=preparation_service_mock, session=session_mock)


@pytest.fixture
def user_repository_mock():
    return Mock()


@pytest.fixture
def user_service(user_repository_mock: Mock, session_mock: MagicMock):
    return UserService(user_repository=user_repository_mock, session=session_mock)