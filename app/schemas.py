from datetime import datetime
from enum import Enum
from pydantic import BaseModel, constr, validator
from typing import Optional
import enum


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class UserBase(BaseModel):
    first_name: constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")
    last_name: constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")
    surname: constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")
    role: UserRole = UserRole.STUDENT


class UserCreateBody(UserBase):
    password: constr(min_length=8, max_length=35)
    group_id: int


class UserCreate(UserBase):
    password: constr(min_length=8, max_length=35)


class UserOut(UserBase):
    id: int
    username: str
    created_at: datetime
    updated_at: datetime
    group_id: Optional[int] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RegistrationToken(Token):
    username: str


class TokenData(BaseModel):
    id: Optional[str] = None


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupOut(GroupBase):
    id: str

    class Config:
        orm_mode = True


class UserEdit(BaseModel):
    id: int
    first_name: Optional[constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")]
    last_name: Optional[constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")]
    surname: Optional[constr(min_length=2, max_length=35, regex="^[а-яА-ЯёЁ]+$")]
    group_id: Optional[int]
    username: Optional[str]


class UserChangePassword(BaseModel):
    password: str
