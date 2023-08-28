# from pydantic import BaseSettings
from typing import Optional
# class Settings(BaseSettings):
#     database_hostname: str
#     database_port: str
#     database_password: str
#     database_name: str
#     database_username: str
#     algorithm: str
#     access_token_secret_key: str
#     access_token_expire_minutes: int
#     database_url: str
#     fastapi_port: int
#     socket_port: int
#     flask_secret_key: str
#     telegram_bot_token: str
#     telegram_chat_id: int
#     pr1_last_step_number: int
#     pr2_last_step_number: int
#     api_url: str
#     socket_url: str
#
#     class Config:
#         env_file = '.env.test'

from dataclasses import dataclass


@dataclass
class BaseClientParameters:
    api_url: str
    socket_url: str


@dataclass
class Settings:
    api_url: str
    socket_url: str
    database_url: str


API_URL='http://localhost:3001'
SOCKET_URL='http://localhost:3002'


settings = Settings(
    api_url=API_URL,
    socket_url=SOCKET_URL,
    database_url='postgresql://postgres:password@localhost:5432/university',
)
