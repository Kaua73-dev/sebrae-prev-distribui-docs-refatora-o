from datetime import datetime

import pytest
from pydantic import ValidationError

from src.exception.prefix import PrefixNotFoundException
from src.schema.request.prefix.prefix_update_request import PrefixUpdateRequest
from src.model.prefix import Prefix
from src.exception.prefix import PrefixAlreadyExistException
from src.schema.request.prefix.prefix_request import PrefixRequest


class TestPrefix:



    def test_create_prefix_with_success(self, prefix_service, prefix_repository_mock):

        request = PrefixRequest(prefix_name="BSB")
        prefix_repository_mock.find_by_prefix_name.return_value = None

        response = prefix_service.create_prefix(request)

        assert response.prefix_name == "BSB"
        prefix_repository_mock.find_by_prefix_name.assert_called_once_with("BSB")
        prefix_repository_mock.save.assert_called_once()

    @pytest.mark.parametrize("prefix_name", [None, ""])
    def test_prefix_request_rejects_invalid_prefix_name(self,prefix_name):
        with pytest.raises(ValidationError):
            PrefixRequest(prefix_name=prefix_name)

    def test_create_prefix_already_exists_exception(self, prefix_service, prefix_repository_mock):

        request = PrefixRequest(prefix_name="BSB")
        prefix_repository_mock.find_by_prefix_name.return_value = object()


        with pytest.raises(PrefixAlreadyExistException):
            prefix_service.create_prefix(request)


        prefix_repository_mock.save.assert_not_called()

    def test_update_prefix_with_success(self, prefix_service, prefix_repository_mock):

        existing_prefix = Prefix()
        existing_prefix.prefix_name = "BSB"
        existing_prefix.required_prefix = True
        existing_prefix.create_at = datetime.now()

        request = PrefixUpdateRequest(prefix_name="BSB", prefix_required=True)
        prefix_repository_mock.find_by_prefix_name.return_value = existing_prefix

        response = prefix_service.update_prefix(request)

        assert response.prefix_name == "BSB"
        assert existing_prefix.required_prefix is True
        prefix_repository_mock.find_by_prefix_name.assert_called_once_with("BSB")
        prefix_repository_mock.save.assert_called_once_with(existing_prefix)

    def test_update_prefix_not_found_throws_exception(self, prefix_service, prefix_repository_mock):
        request = PrefixUpdateRequest(prefix_name="BSB", prefix_required=True)
        prefix_repository_mock.find_by_prefix_name.return_value = None

        with pytest.raises(PrefixNotFoundException):
            prefix_service.update_prefix(request)


        prefix_repository_mock.assert_not_called()

    def test_find_all_prefix_with_success(self, prefix_service, prefix_repository_mock):

        prefix_1 = Prefix()
        prefix_1.prefix_name = "BSB"
        prefix_1.required_prefix = True
        prefix_1.create_at = datetime.now()

        prefix_2 = Prefix()
        prefix_2.prefix_name = "SP"
        prefix_2.required_prefix = False
        prefix_2.create_at = datetime.now()

        prefix_repository_mock.find_all.return_value = [prefix_1, prefix_2]

        response = prefix_service.find_all_prefixes()

        assert len(response) == 2
        assert response[0].prefix_name == "BSB"
        assert response[1].prefix_name == "SP"
        prefix_repository_mock.find_all.assert_called_once()

    def test_find_all_prefix_returns_empty_list(self, prefix_service, prefix_repository_mock):
        prefix_repository_mock.find_all.return_value = []

        response = prefix_service.find_all_prefixes()

        assert response == []
        prefix_repository_mock.find_all.assert_called_once()

    def test_find_prefix_required_true_with_success(self, prefix_service, prefix_repository_mock):

        prefix_1 = Prefix()
        prefix_1.prefix_name = "BSB"
        prefix_1.required_prefix = True
        prefix_1.create_at = datetime.now()

        prefix_repository_mock.find_by_required_prefix_true_order_by_name.return_value = [prefix_1]

        response = prefix_service.find_prefix_required_true()

        assert len(response) == 1
        assert response[0].prefix_name == "BSB"
        assert response[0].required_prefix is True
        prefix_repository_mock.find_by_required_prefix_true_order_by_name.assert_called_once()

