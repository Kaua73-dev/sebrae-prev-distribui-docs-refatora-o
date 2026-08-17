from pathlib import Path
from src.core.config import settings
from src.repository.user_email import UserEmailRepository
from src.service.preparation.file_block import FileBlock

class PreparationService:

    def __init__(self, prefix_service, user_email_repository: UserEmailRepository):
        self.prefix_service = prefix_service
        self.user_email_repository = user_email_repository


    def mount_block_files(self) -> list[FileBlock]:

        all_files = self._get_files()
        prefixes_actives = self.prefix_service.find_prefix_required_true()

        email_by_prefix = {
            user_email.prefix.prefix_name: user_email.email
            for user_email in self.user_email_repository.find_by_is_active_true()
        }

        blocks = []
        for prefix in prefixes_actives:
            files_of_block = [
                path
                for path in all_files
                if self._belong_in_prefix(path.name, prefix.prefix_name)
            ]
            blocks.append(FileBlock(
                prefix=prefix.prefix_name,
                files=files_of_block,
                email=email_by_prefix.get(prefix.prefix_name),
            ))
        return blocks

    @staticmethod
    def _get_files() -> list[Path]:
        base_path = Path(settings.FILES_DIR_PATH)

        files_accepted = (".pdf", ".xls", ".xlsx", ".txt")

        return [
            files_path
            for files_path in base_path.rglob("*")
            if files_path.is_file() and files_path.suffix.lower() in files_accepted
        ]

    @staticmethod
    def _belong_in_prefix(file_name: str, prefix: str) -> bool:

        if not file_name.startswith(prefix):
            return False

        if len(file_name) == len(prefix):
            return False

        next_char = file_name[len(prefix)]
        return not next_char.isalpha()
