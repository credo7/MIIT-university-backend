from pydantic import BaseSettings


class Settings(BaseSettings):
    api_port: int = 8000
    database_url: str
    access_token_secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Настройки логирования
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file: str = "../app.log"

    class Config:
        env_file = '.env'


settings = Settings()
