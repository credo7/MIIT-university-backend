from pydantic import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    algorithm: str
    access_token_secret_key: str
    access_token_expire_minutes: int
    database_url: str
    fastapi_port: int
    socket_port: int
    flask_secret_key: str
    telegram_bot_token: str
    telegram_chat_id: int
    pr1_last_step_number: int
    pr2_last_step_number: int

    class Config:
        env_file = '.env'


settings = Settings()
