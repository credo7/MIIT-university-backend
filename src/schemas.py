import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr, conint


class UserRole(str, enum.Enum):
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'


class UserBase(BaseModel):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    surname: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    role: UserRole = UserRole.STUDENT


class UserCreateBody(UserBase):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    password: constr(min_length=8, max_length=35)
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    group_id: int


class UserCreate(UserBase):
    password: constr(min_length=8, max_length=35)


class UserOut(UserBase):
    id: int
    # username: str
    first_name: str
    last_name: str
    surname: Optional[str]
    # created_at: datetime
    # updated_at: datetime
    approved: bool
    group_name: Optional[str] = None
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
    first_name: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    last_name: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    group_id: Optional[int]
    username: Optional[str]


class ResponseMessage(BaseModel):
    message: str


class UserToApprove(BaseModel):
    id: int
    first_name: str
    last_name: str
    surname: Optional[str]
    group_name: str


class UserChangePassword(BaseModel):
    password: str


class CheckpointData(BaseModel):
    event_id: int
    step: conint(ge=0)
    points: conint(ge=0)
    fails: conint(ge=0)


class EventMode(str, enum.Enum):
    CLASS = "CLASS"
    CONTROL = "CONTROL"
    WORKOUT = "WORKOUT"


class StartEventComputer(BaseModel):
    id: int
    type: int
    mode: EventMode

