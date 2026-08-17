from pathlib import Path

from src.core.config import settings
from src.repository.user_email import UserEmailRepository
from src.service.preparation.file_block import FileBlock

ACCEPTED_SUFFIXES = (".pdf", ".xls", ".xlsx", ".txt")


class PreparationService:




    def __init__(self, prefix_service, user_email_repository: UserEmailRepository):
        self.prefix_service = prefix_service
        self.user_email_repository = user_email_repository




    def mount_block_files(self) -> list[FileBlock]:
        all_files = self._get_files()
        email_by_prefix = self._email_by_prefix()

        return [
            FileBlock(
                prefix=prefix.prefix_name,
                files=self._files_of_prefix(all_files, prefix.prefix_name),
                email=email_by_prefix.get(prefix.prefix_name),
            )
            for prefix in self.prefix_service.find_prefix_required_true()
        ]

    def find_files_without_prefix(self, blocks: list[FileBlock]) -> list[Path]:
        grouped = {file for block in blocks for file in block.files}
        return [file for file in self._get_files() if file not in grouped]



    def _email_by_prefix(self) -> dict[str, str]:
        return {
            user_email.prefix.prefix_name: user_email.email
            for user_email in self.user_email_repository.find_by_is_active_true()
        }

    def _files_of_prefix(self, all_files: list[Path], prefix: str) -> list[Path]:
        return [file for file in all_files if self._belongs_to_prefix(file.name, prefix)]

    @staticmethod
    def _get_files() -> list[Path]:
        base_path = Path(settings.FILES_DIR_PATH)

        return [
            file
            for file in base_path.rglob("*")
            if file.is_file() and file.suffix.lower() in ACCEPTED_SUFFIXES
        ]

    @staticmethod
    def _belongs_to_prefix(file_name: str, prefix: str) -> bool:
        if not file_name.startswith(prefix):
            return False

        remainder = file_name[len(prefix):]

        return bool(remainder) and not remainder[0].isalpha()
