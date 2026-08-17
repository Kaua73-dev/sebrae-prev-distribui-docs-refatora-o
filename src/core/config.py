from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_ECHO: bool = False

    FILES_DIR_PATH: str

    MAIL_HOST: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "nao-responda@sebraeprev.com.br"
    MAIL_FROM_NAME: str = "Distribui Docs"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    MAIL_SENDING_DISABLED: bool = True
    MAIL_REDIRECT_ALL_TO: str = ""
    MAIL_MAX_ATTACHMENT_MB: int = 20

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def mail_is_redirected(self) -> bool:
        return bool(self.MAIL_REDIRECT_ALL_TO)

    @property
    def mail_max_attachment_bytes(self) -> int:
        return self.MAIL_MAX_ATTACHMENT_MB * 1024 * 1024


settings = Settings()
