from src.schema.request.prefix.prefix_request import PrefixRequest


class TestCreatePrefix:






    def test_create_prefix_with_success(self, prefix_service, prefix_repository_mock):

        request = PrefixRequest(prefix_name="BSB")
        prefix_repository_mock.find_by_prefix_name.return_value = None

        response = prefix_service.create_prefix(request)

        assert response.prefix_name == "BSB"
        prefix_repository_mock.find_by_prefix_name.assert_called_once_with("BSB")
        prefix_repository_mock.save.assert_called_once()

