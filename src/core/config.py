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
    
    model_config = SettingsConfigDict(env_file=".env") 
       
settings = Settings()   