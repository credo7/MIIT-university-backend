import enum
from datetime import datetime
from typing import Optional, Any, List, Dict
from bson import ObjectId

from pydantic import BaseModel, constr, conint
from pydantic.class_validators import validator

from strenum import StrEnum


# TODO: Think about it
# class CustomBaseModel(BaseModel):
#     class Config:
#         json_encoders = {ObjectId: lambda x: str(x)}
#         alias_generator = lambda string: string.replace("_id", "id")
#
#     @validator(pre=True, always=True)
#     def parse_object_ids(cls, values):
#         result = {}
#         for field_name, value in values.items():
#             if isinstance(value, str) and (field_name == "id" or field_name.endswith("_id")):
#                 result[field_name] = ObjectId(value)
#             else:
#                 result[field_name] = value
#         return result


class Incoterm(StrEnum):
    EXW = "EXW"
    FCA = "FCA"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"
    FAS = "FAS"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"


class WSCommandTypes(StrEnum):
    SELECT_TYPE = 'SELECT_TYPE'
    START = 'START'


class EventType(enum.IntEnum):
    PR1 = 1
    PR2 = 2
    CONTROL = 3


class EventMode(StrEnum):
    CLASS = "CLASS"
    EXAM = "EXAM"
    WORKOUT = "WORKOUT"


class GeneralStep(BaseModel):
    id: int
    name: str


class EventStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    FINISHED = "FINISHED"


class ConnectedComputer(BaseModel):
    id: int
    users_ids: List[str]
    event_type: EventType
    event_mode: EventMode
    is_connected: bool
    status: EventStatus = EventStatus.NOT_STARTED.value


class ConnectedComputerEdit(BaseModel):
    id: int
    users_ids: Optional[List[str]]
    event_type: Optional[EventType]
    event_mode: Optional[EventMode]
    step: Optional[GeneralStep]
    is_connected: Optional[bool]
    status: Optional[EventStatus]


class WSMessage(BaseModel):
    type: WSCommandTypes
    payload: Any


class UserRole(str, enum.Enum):
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'


class Lesson(BaseModel):
    id: Optional[str]
    group_id: str
    group_name: str
    event_mode: Optional[EventMode]
    event_type: Optional[EventType]
    created_at: datetime = datetime.now()


class UserBase(BaseModel):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    surname: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')


class UserCreateBody(UserBase):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    password: constr(min_length=8, max_length=35)
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    group_id: str


class UserEventHistory(BaseModel):
    event_id: str
    points: int
    fails: int


class UserCreateDB(UserCreateBody):
    password: str
    username: str
    role: UserRole = UserRole.STUDENT
    group_name: str
    history: List[UserEventHistory] = []


class FullUser(UserCreateDB):
    id: str
    approved: bool


class UserOut(UserBase):
    id: str
    first_name: str
    last_name: str
    surname: Optional[str]
    approved: bool = False
    group_name: Optional[str] = None
    group_id: Optional[str] = None


class UserEvent(BaseModel):
    event_type: EventType
    event_mode: EventMode
    points: int
    lesson_id: str
    created_at: datetime = datetime.now()


class UserOutWithEvents(UserOut):
    events_history: Optional[List[UserEvent]] = []


class UserSearch(BaseModel):
    search: Optional[str]
    group_id: Optional[str]
    group_name: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str


class RegistrationResponse(Token):
    username: str
    user_info: UserOut


class LoginResponse(Token):
    user_info: UserOutWithEvents


class TokenData(BaseModel):
    id: Optional[str] = None


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupOut(GroupBase):
    id: str


class PracticeOneBet(BaseModel):
    name: str
    rate: int


class EventCheckpoint(BaseModel):
    step_id: int
    user_ids: List[str]
    points: int
    fails: int


class EventResult(UserBase):
    group_name: str
    username: str
    fails: int
    points: int


class EventStepResult(BaseModel):
    step_index: int
    user_ids: List[str]
    points: int
    fails: int


class EventInfo(BaseModel):
    lesson_id: str
    computer_id: int
    is_finished: bool = False
    event_type: EventType
    event_mode: EventMode
    created_at: datetime = datetime.now()
    users_ids: List[str]
    checkpoints: List[EventCheckpoint] = []
    steps_results: List[EventStepResult]
    results: List[EventResult]
    step_index: int = 1


class PracticeOneVariant(EventInfo):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    incoterms: List[Incoterm]
    bets: List[PracticeOneBet]


class QuestionOption(BaseModel):
    value: str
    is_correct: bool


class TestQuestionPR1(BaseModel):
    question: str
    options: List[QuestionOption]


class StepRole(StrEnum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    ALL = "ALL"


class Step(BaseModel):
    index: int
    code: str
    name: str
    role: StepRole


class BetInfoValuePR1(BaseModel):
    min: int
    max: int
    step: int


class BetInfoIncotermsRolePR1(BaseModel):
    buyer: List[Incoterm]
    seller: List[Incoterm]


class BetInfoPR1(BaseModel):
    name: str
    value: BetInfoValuePR1
    incoterms: BetInfoIncotermsRolePR1


class PracticeOneInfo(BaseModel):
    legend_pattern: str
    all_incoterms: List[str]
    steps: List[Step]
    test_questions: List[TestQuestionPR1]
    bets: List[BetInfoPR1]


class UserCredentials(BaseModel):
    username: str
    password: str


class UserUpdate(UserBase):
    id: int
    group_id: Optional[str]
    group_name: Optional[str]
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
    computer_id: int
    points: conint(ge=0)
    fails: conint(ge=0)


class JoinData(BaseModel):
    computer_id: conint(ge=0)
    user_id: conint(ge=0)


class StartEventComputer(BaseModel):
    computer_id: int
    type: int
    mode: EventMode
