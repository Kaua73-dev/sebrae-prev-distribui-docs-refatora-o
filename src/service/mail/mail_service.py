from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.core.config import settings
from src.core.paths import TEMPLATE_DIR

connection_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_HOST or "localhost",
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    SUPPRESS_SEND=1 if settings.MAIL_SENDING_DISABLED else 0,
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)


class MailService:

    TEMPLATE_NAME = "dispatch_email.html"

    def __init__(self, mail: FastMail | None = None):
        self.mail = mail or FastMail(connection_config)



    async def send_files(self, prefix_name: str, intended_recipient: str, files: list[Path]) -> str:
        actual_recipient = self.actual_recipient_for(intended_recipient)
        message = self._build_message(prefix_name, intended_recipient, actual_recipient, files)

        await self.mail.send_message(message, template_name=self.TEMPLATE_NAME)

        return actual_recipient

    @staticmethod
    def actual_recipient_for(intended_recipient: str) -> str:
        return settings.MAIL_REDIRECT_ALL_TO or intended_recipient

    def _build_message(self,prefix_name: str,intended_recipient: str,actual_recipient: str, files: list[Path]) -> MessageSchema:
        return MessageSchema(
            subject=self._build_subject(prefix_name, intended_recipient),
            recipients=[actual_recipient],
            template_body={
                "prefix_name": prefix_name,
                "file_names": [file.name for file in files],
                "intended_recipient": intended_recipient,
                "is_redirected": settings.mail_is_redirected,
            },
            subtype=MessageType.html,
            attachments=[str(file) for file in files],
        )

    @staticmethod
    def _build_subject(prefix_name: str, intended_recipient: str) -> str:
        subject = f"Arquivos {prefix_name}"

        if settings.mail_is_redirected:
            return f"[TESTE -> {intended_recipient}] {subject}"

        return subject
