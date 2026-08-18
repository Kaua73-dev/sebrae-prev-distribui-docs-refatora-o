from pathlib import Path

from src.core.config import settings
from src.model.dispatch import Dispatch, DispatchBlock


class PreFlightCheck:

    def __init__(self, dispatch: Dispatch, files_without_prefix: list[Path] | None = None):
        self.dispatch = dispatch
        self.files_without_prefix = files_without_prefix or []





    def warnings(self) -> list[str]:
        block_warnings = [
            warning
            for block in sorted(self.dispatch.included_blocks, key=lambda block: block.prefix_name)
            for warning in self._warnings_for(block)
        ]
        return block_warnings + self._warnings_for_files_without_prefix()

    def _warnings_for(self, block: DispatchBlock) -> list[str]:
        checks = (
            self._missing_recipient(block),
            self._empty_block(block),
            self._vanished_files(block),
            self._oversized_attachments(block),
        )
        return [warning for warning in checks if warning is not None]

    @staticmethod
    def _missing_recipient(block: DispatchBlock) -> str | None:
        if block.intended_recipient is not None:
            return None
        return f"{block.prefix_name}: sem email cadastrado, nao sera enviado"

    @staticmethod
    def _empty_block(block: DispatchBlock) -> str | None:
        if block.file_paths:
            return None
        return f"{block.prefix_name}: nenhum arquivo encontrado"

    @staticmethod
    def _vanished_files(block: DispatchBlock) -> str | None:
        vanished = [file for file in block.files if not file.exists()]

        if not vanished:
            return None

        return (
            f"{block.prefix_name}: {len(vanished)} arquivo(s) sumiram da pasta "
            f"desde a preparacao"
        )

    @staticmethod
    def _oversized_attachments(block: DispatchBlock) -> str | None:
        total_bytes = sum(file.stat().st_size for file in block.files if file.exists())

        if total_bytes <= settings.mail_max_attachment_bytes:
            return None

        return (
            f"{block.prefix_name}: anexos somam {total_bytes / 1024 / 1024:.1f}MB, "
            f"acima do limite de {settings.MAIL_MAX_ATTACHMENT_MB}MB"
        )

    def _warnings_for_files_without_prefix(self) -> list[str]:
        if not self.files_without_prefix:
            return []

        names = ", ".join(file.name for file in self.files_without_prefix)
        return [
            f"{len(self.files_without_prefix)} arquivo(s) fora de qualquer bloco "
            f"(prefixo nao cadastrado): {names}"
        ]
