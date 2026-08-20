from unittest.mock import Mock, MagicMock

import pytest

from src.service.prefix.prefix_service import PrefixService


@pytest.fixture
def prefix_repository_mock():
    return Mock()

@pytest.fixture
def session_mock():
    return MagicMock()

@pytest.fixture
def prefix_service(prefix_repository_mock: Mock, session_mock: Mock):
    return PrefixService(prefix_repository=prefix_repository_mock, session=session_mock)

