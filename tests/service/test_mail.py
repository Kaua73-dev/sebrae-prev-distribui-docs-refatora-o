import pytest

from src.core.config import settings
from src.service.mail import MailService

INTENDED = "bsb@sebraeprev.com.br"
REDIRECT = "teste@sebraeprev.com.br"



@pytest.fixture
def files(tmp_path):
    first = tmp_path / "BSB_001.pdf"
    second = tmp_path / "BSB_002.xlsx"

    first.touch()
    second.touch()

    return [first, second]


def sent_message(mail_mock):
    return mail_mock.send_message.call_args.args[0]


class TestMailService:




    def test_actual_recipient_for_returns_the_intended_when_there_is_no_redirect(self, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", "")

        assert MailService.actual_recipient_for(INTENDED) == INTENDED

    def test_actual_recipient_for_returns_the_redirect_when_it_is_set(self, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", REDIRECT)

        assert MailService.actual_recipient_for(INTENDED) == REDIRECT

    def test_build_subject_without_redirect(self, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", "")

        assert MailService._build_subject("BSB", INTENDED) == "Arquivos BSB"

    def test_build_subject_with_redirect_flags_the_intended_recipient(self, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", REDIRECT)

        assert MailService._build_subject("BSB", INTENDED) == f"[TESTE -> {INTENDED}] Arquivos BSB"

    async def test_send_files_sends_to_the_intended_recipient(self, mail_service, mail_mock, files, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", "")

        delivered_to = await mail_service.send_files("BSB", INTENDED, files)

        assert delivered_to == INTENDED

        message = sent_message(mail_mock)
        assert [recipient.email for recipient in message.recipients] == [INTENDED]
        assert message.subject == "Arquivos BSB"
        assert message.template_body["is_redirected"] is False

        mail_mock.send_message.assert_awaited_once()
        assert mail_mock.send_message.call_args.kwargs["template_name"] == MailService.TEMPLATE_NAME

    async def test_send_files_sends_only_to_the_redirect_address(self, mail_service, mail_mock, files, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", REDIRECT)

        delivered_to = await mail_service.send_files("BSB", INTENDED, files)

        assert delivered_to == REDIRECT

        message = sent_message(mail_mock)
        recipients = [recipient.email for recipient in message.recipients]

        assert recipients == [REDIRECT]
        assert INTENDED not in recipients
        assert message.template_body["intended_recipient"] == INTENDED
        assert message.template_body["is_redirected"] is True

    async def test_send_files_attaches_every_file(self, mail_service, mail_mock, files, monkeypatch):
        monkeypatch.setattr(settings, "MAIL_REDIRECT_ALL_TO", "")

        await mail_service.send_files("BSB", INTENDED, files)

        message = sent_message(mail_mock)

        assert message.template_body["prefix_name"] == "BSB"
        assert message.template_body["file_names"] == ["BSB_001.pdf", "BSB_002.xlsx"]

        # O fastapi-mail transforma cada anexo em uma tupla (UploadFile, headers).
        assert [attachment[0].filename for attachment in message.attachments] == ["BSB_001.pdf", "BSB_002.xlsx"]
