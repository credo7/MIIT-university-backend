from pydantic import BaseSettings

class Settings(BaseSettings):
    api_port: int
    database_url: str
    access_token_secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    telegram_bot_token: str
    telegram_chat_id: int

    class Config:
        env_file = '.env'


settings = Settings()
