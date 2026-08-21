from datetime import datetime

import pytest

from src.core.config import settings
from src.model.prefix import Prefix
from src.model.user_email import UserEmail
from src.schema.response.prefix import PrefixResponse
from src.service.preparation.preparation_service import PreparationService



@pytest.fixture
def files_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILES_DIR_PATH", str(tmp_path))
    return tmp_path


def create_prefix_response(prefix_name: str) -> PrefixResponse:
    return PrefixResponse(prefix_name=prefix_name, required_prefix=True, create_at=datetime.now())


def create_active_user_email(email: str, prefix_name: str) -> UserEmail:
    prefix = Prefix()
    prefix.prefix_name = prefix_name

    user_email = UserEmail()
    user_email.email = email
    user_email.prefix = prefix

    return user_email


class TestPreparationService:




    @pytest.mark.parametrize(
        "file_name, prefix, expected",
        [
            ("BSB_001.pdf", "BSB", True),
            ("BSB-001.xlsx", "BSB", True),
            ("BSB 001.txt", "BSB", True),
            ("BSB.pdf", "BSB", True),
            ("BSB1_001.pdf", "BSB", True),
            ("BSBSUL_001.pdf", "BSB", False),
            ("SP_001.pdf", "BSB", False),
            ("bsb_001.pdf", "BSB", False),
            ("BSB", "BSB", False),
        ],
    )
    def test_belongs_to_prefix_accepts_only_the_exact_prefix(self, file_name, prefix, expected):
        assert PreparationService._belongs_to_prefix(file_name, prefix) is expected

    def test_mount_block_files_groups_files_by_prefix(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()
        (files_dir / "BSB_002.xlsx").touch()
        (files_dir / "SP_001.pdf").touch()

        prefix_service_mock.find_prefix_required_true.return_value = [
            create_prefix_response("BSB"),
            create_prefix_response("SP"),
        ]
        user_email_repository_mock.find_by_is_active_true.return_value = [
            create_active_user_email("bsb@sebraeprev.com.br", "BSB"),
            create_active_user_email("sp@sebraeprev.com.br", "SP"),
        ]

        blocks = preparation_service.mount_block_files()

        assert len(blocks) == 2

        assert blocks[0].prefix == "BSB"
        assert blocks[0].email == "bsb@sebraeprev.com.br"
        assert sorted(file.name for file in blocks[0].files) == ["BSB_001.pdf", "BSB_002.xlsx"]

        assert blocks[1].prefix == "SP"
        assert blocks[1].email == "sp@sebraeprev.com.br"
        assert [file.name for file in blocks[1].files] == ["SP_001.pdf"]

        prefix_service_mock.find_prefix_required_true.assert_called_once()
        user_email_repository_mock.find_by_is_active_true.assert_called_once()

    def test_mount_block_files_ignores_unsupported_suffixes(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()
        (files_dir / "BSB_002.docx").touch()
        (files_dir / "BSB_003.zip").touch()

        prefix_service_mock.find_prefix_required_true.return_value = [create_prefix_response("BSB")]
        user_email_repository_mock.find_by_is_active_true.return_value = []

        blocks = preparation_service.mount_block_files()

        assert [file.name for file in blocks[0].files] == ["BSB_001.pdf"]

    def test_mount_block_files_with_prefix_without_active_email(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()

        prefix_service_mock.find_prefix_required_true.return_value = [create_prefix_response("BSB")]
        user_email_repository_mock.find_by_is_active_true.return_value = []

        blocks = preparation_service.mount_block_files()

        assert len(blocks) == 1
        assert blocks[0].prefix == "BSB"
        assert blocks[0].email is None
        assert len(blocks[0].files) == 1

    def test_mount_block_files_returns_empty_list_when_there_is_no_required_prefix(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()

        prefix_service_mock.find_prefix_required_true.return_value = []
        user_email_repository_mock.find_by_is_active_true.return_value = []

        blocks = preparation_service.mount_block_files()

        assert blocks == []

    def test_find_files_without_prefix_returns_the_leftovers(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()
        (files_dir / "sem_prefixo.pdf").touch()
        (files_dir / "BSBSUL_001.pdf").touch()

        prefix_service_mock.find_prefix_required_true.return_value = [create_prefix_response("BSB")]
        user_email_repository_mock.find_by_is_active_true.return_value = []

        blocks = preparation_service.mount_block_files()
        without_prefix = preparation_service.find_files_without_prefix(blocks)

        assert sorted(file.name for file in without_prefix) == ["BSBSUL_001.pdf", "sem_prefixo.pdf"]

    def test_find_files_without_prefix_returns_empty_list_when_every_file_is_grouped(self, files_dir, preparation_service, prefix_service_mock, user_email_repository_mock):

        (files_dir / "BSB_001.pdf").touch()

        prefix_service_mock.find_prefix_required_true.return_value = [create_prefix_response("BSB")]
        user_email_repository_mock.find_by_is_active_true.return_value = []

        blocks = preparation_service.mount_block_files()

        assert preparation_service.find_files_without_prefix(blocks) == []
