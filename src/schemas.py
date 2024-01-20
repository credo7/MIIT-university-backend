import enum
from datetime import datetime
from typing import Optional, Any, List, Dict
from bson import ObjectId

from pydantic import BaseModel, constr, conint
from pydantic.class_validators import validator


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


class Incoterm(str, enum.Enum):
    EXW = 'EXW'
    FCA = 'FCA'
    CPT = 'CPT'
    CIP = 'CIP'
    DAP = 'DAP'
    DPU = 'DPU'
    DDP = 'DDP'
    FAS = 'FAS'
    FOB = 'FOB'
    CFR = 'CFR'
    CIF = 'CIF'


class WSCommandTypes(str, enum.Enum):
    SELECT_TYPE = 'SELECT_TYPE'
    START = 'START'
    RAISE_HAND = 'RAISE_HAND'
    FINISH = 'FINISH'
    EXIT = 'EXIT'


class EventType(str, enum.Enum):
    PR1 = 'PR1'
    PR2 = 'PR2'
    CONTROL = 'CONTROL'


class EventMode(str, enum.Enum):
    CLASS = 'CLASS'
    EXAM = 'EXAM'
    WORKOUT = 'WORKOUT'


class GeneralStep(BaseModel):
    id: int
    name: str


class EventStatus(str, enum.Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'


class ConnectedComputer(BaseModel):
    id: int
    users_ids: List[str]
    event_type: Optional[EventType]
    event_mode: Optional[EventMode]
    is_connected: bool
    step: Optional[GeneralStep]
    status: EventStatus = EventStatus.NOT_STARTED.value


class ActualizeComputerPayload(BaseModel):
    event_type: EventType
    event_mode: EventMode


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
    payload: Optional[Any]


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
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]


class UserCreateBody(UserBase):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    password: constr(min_length=8, max_length=35)
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')]
    group_id: str


class UserEventHistory(BaseModel):
    lesson_id: str
    event_id: str
    event_type: EventType
    event_mode: EventMode
    is_failed: Optional[bool] = False
    points: int = 0
    fails: int = 0
    finished_at: datetime = datetime.now()


class UserCreateDB(UserCreateBody):
    password: str
    username: str
    role: UserRole = UserRole.STUDENT
    group_name: str
    approved: bool = False
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
    role: UserRole = UserRole.STUDENT.value
    incoterms: Dict[Incoterm, int] = {}


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
    description: Optional[str]


class EventInfo(BaseModel):
    id: Optional[str]
    lesson_id: str
    computer_id: int
    is_finished: bool = False
    event_type: EventType
    event_mode: EventMode
    created_at: datetime = datetime.now()
    users_ids: List[str]
    checkpoints: List[EventCheckpoint] = []
    steps_results: List[EventStepResult] = []
    results: List[EventResult] = []
    step_index: int = 1


class BetsRolePR1(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'


class BetInfoIncotermsRolePR1(BaseModel):
    buyer: List[Incoterm]
    seller: List[Incoterm]


class PracticeOneBet(BaseModel):
    name: str
    rate: int
    bet_pattern: BetInfoIncotermsRolePR1


class PracticeOneBetOut(BaseModel):
    name: str
    rate: int
    is_correct: bool


class TablePR1(BaseModel):
    index: int
    role: BetsRolePR1
    incoterm: Incoterm
    bets: List[PracticeOneBetOut]


class Logist(BaseModel):
    description: str


class OptionPR1(BaseModel):
    buyer: int
    seller: int
    total: int
    incoterm: Incoterm


class QuestionOption(BaseModel):
    value: str
    is_correct: bool = False


class TestQuestionPR1(BaseModel):
    question: str
    options: List[QuestionOption]
    incoterm: Optional[Incoterm]


class PracticeOneVariables(BaseModel):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    incoterms: List[Incoterm]
    bets: List[PracticeOneBet]


class ExamInputVariablesPR1(BaseModel):
    product_price: int
    total_products: int
    packaging: int
    product_examination: int
    loading_during_transport: int
    unloading_during_transport: int
    main_delivery: int
    export_customs_formalities_and_payments: int
    delivery_to_port: int
    loading_on_board: int
    transport_to_destination: int
    delivery_to_carrier: int
    insurance: int
    # Расходы на разгрузку, которые по договору перевозки относятся к продавцу
    unloading_seller_agreement: int
    import_customs_formalities_and_payments: int
    transport_to_terminal: int
    unloading_on_terminal: int


class ExamInputPR1(BaseModel):
    legend: str
    to_point: str
    from_point: str
    product_name: str
    variables: ExamInputVariablesPR1


class PracticeOneExamVariant(EventInfo, ExamInputPR1):
    answers: dict[Incoterm, int]



class PracticeOneVariant(EventInfo):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    incoterms: List[Incoterm]
    tables: Dict[BetsRolePR1, List[TablePR1]]
    logists: List[Logist]
    options: List[OptionPR1]
    tests: List[TestQuestionPR1]


class StepRole(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ALL = 'ALL'


class Step(BaseModel):
    index: int
    code: str
    name: str
    role: StepRole


class ExamStep(BaseModel):
    index: int
    code: str
    name: str


class BetInfoValuePR1(BaseModel):
    min: int
    max: int


class BetInfoPR1(BaseModel):
    name: str
    value_percentage: BetInfoValuePR1
    incoterms: BetInfoIncotermsRolePR1


class ClassicTestQuestionBlock(BaseModel):
    first_block: List[TestQuestionPR1]
    second_block: List[TestQuestionPR1]
    third_block: Dict[Incoterm, List[TestQuestionPR1]]


class PracticeOneInfo(BaseModel):
    legend_pattern: str
    all_incoterms: List[str]
    steps: List[Step]
    exam_steps: List[ExamStep]
    bets: List[BetInfoPR1]
    logists: List[str]
    classic_test_questions: ClassicTestQuestionBlock
    control_test_questions: list[TestQuestionPR1]


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
    points: conint(ge=0)
    fails: conint(ge=0)
    description: Optional[str]


class JoinData(BaseModel):
    computer_id: conint(ge=0)
    user_id: conint(ge=0)


class StartEventComputer(BaseModel):
    computer_id: int
    type: int
    mode: EventMode
