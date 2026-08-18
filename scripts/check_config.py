from src.core.config import settings


print(settings.APP_NAME)
print(settings.DB_NAME)
print(settings.DB_PORT, type(settings.DB_PORT))
print(settings.DB_ECHO, type(settings.DB_ECHO))