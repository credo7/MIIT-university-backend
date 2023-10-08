from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    algorithm: str
    access_token_secret_key: str
    access_token_expire_minutes: int
    database_url: str
    fastapi_port: int
    socket_port: int
    database_url: str

    class Config:
        env_file = '.env'


settings = Settings()
