import enum
import random
import time
from abc import ABCMeta, ABC, abstractmethod
from datetime import datetime
from typing import (
    Any,
    Optional,
    Union,
)

from bson import ObjectId
from pydantic import (
    BaseModel,
    Field,
    conint,
    constr,
)
from pydantic.class_validators import validator
from typing_extensions import Annotated


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


class AnswerStatus(str, enum.Enum):
    CORRECT = 'CORRECT'
    CORRECT_WITH_FAILS = 'CORRECT_WITH_FAILS'
    FAILED = 'FAILED'


class CorrectOrError(str, enum.Enum):
    ERROR = 'ERROR'
    CORRECT = 'CORRECT'


class TextType(str, enum.Enum):
    text = 'text'
    dash = 'dash'
    enumerated = 'enumerated'


class AllowedModes(str, enum.Enum):
    PR1_CLASS = 'PR1_CLASS'
    PR1_CONTROL = 'PR1_CONTROL'
    PR2_CLASS = 'PR2_CLASS'


class PR1ClassBetType(str, enum.Enum):
    COMMON = 'COMMON'
    BUYER = 'BUYER'
    SELLER = 'SELLER'


class CheckpointResponseStatus(str, enum.Enum):
    SUCCESS = 'SUCCESS'
    TRY_AGAIN = 'TRY_AGAIN'
    FAILED = 'FAILED'


class PR2PointsCodes(str, enum.Enum):
    CHINA_SHIJIAZHUANG_DEPARTURE_POINT = 'CHINA_SHIJIAZHUANG_DEPARTURE_POINT'
    CHINA_JINAN_DEPARTURE_POINT = 'CHINA_JINAN_DEPARTURE_POINT'
    CHINA_YIWU_DEPARTURE_POINT = 'CHINA_YIWU_DEPARTURE_POINT'
    CHINA_BAODING_DEPARTURE_POINT = 'CHINA_BAODING_DEPARTURE_POINT'
    JAPAN_KYOTO_DEPARTURE_POINT = 'JAPAN_KYOTO_DEPARTURE_POINT'
    JAPAN_AYABE_DEPARTURE_POINT = 'JAPAN_AYABE_DEPARTURE_POINT'
    JAPAN_ASAGO_DEPARTURE_POINT = 'JAPAN_ASAGO_DEPARTURE_POINT'
    JAPAN_MATSUMOTO_DEPARTURE_POINT = 'JAPAN_MATSUMOTO_DEPARTURE_POINT'
    SOUTH_KOREA_SUWON_SI_DEPARTURE_POINT = 'SOUTH_KOREA_SUWON_SI_DEPARTURE_POINT'
    SOUTH_KOREA_DAEJEON_DEPARTURE_POINT = 'SOUTH_KOREA_DAEJEON_DEPARTURE_POINT'
    SOUTH_KOREA_CHANGWON_SI_DEPARTURE_POINT = 'SOUTH_KOREA_CHANGWON_SI_DEPARTURE_POINT'
    SOUTH_KOREA_GWANGJU_DEPARTURE_POINT = 'SOUTH_KOREA_GWANGJU_DEPARTURE_POINT'
    POLAND_LODZ_DESTINATION_POINT = 'POLAND_LODZ_DESTINATION_POINT'
    POLAND_OSTRAVA_DESTINATION_POINT = 'POLAND_OSTRAVA_DESTINATION_POINT'
    GERMAN_LEIPZIG_DESTINATION_POINT = 'GERMAN_LEIPZIG_DESTINATION_POINT'
    GERMAN_AUGSBURG_DESTINATION_POINT = 'GERMAN_AUGSBURG_DESTINATION_POINT'
    FRANCE_LYON_DESTINATION_POINT = 'FRANCE_LYON_DESTINATION_POINT'
    FRANCE_ROUEN_DESTINATION_POINT = 'FRANCE_ROUEN_DESTINATION_POINT'
    NETHERLANDS_UTRETCH_DESTINATION_POINT = 'NETHERLANDS_UTRETCH_DESTINATION_POINT'
    NETHERLANDS_HARLEM_DESTINATION_POINT = 'NETHERLANDS_HARLEM_DESTINATION_POINT'
    BELGIUM_LEUVEN_DESTINATION_POINT = 'BELGIUM_LEUVEN_DESTINATION_POINT'
    BELGIUM_GENT_DESTINATION_POINT = 'BELGIUM_GENT_DESTINATION_POINT'
    CZECH_PARDUBICE_DESTINATION_POINT = 'CZECH_PARDUBICE_DESTINATION_POINT'
    CZECH_PILSEN_DESTINATION_POINT = 'CZECH_PILSEN_DESTINATION_POINT'
    AUSTRIA_LINZ_DESTINATION_POINT = 'AUSTRIA_LINZ_DESTINATION_POINT'
    AUSTRIA_SAINT_POLTEN_DESTINATION_POINT = 'AUSTRIA_SAINT_POLTEN_DESTINATION_POINT'
    CHINA_GUANGZHOU_PORT = 'CHINA_GUANGZHOU_PORT'
    CHINA_NINGBO_PORT = 'CHINA_NINGBO_PORT'
    CHINA_CHONGQING_PORT = 'CHINA_CHONGQING_PORT'
    CHINA_QINGDAO_PORT = 'CHINA_QINGDAO_PORT'
    JAPAN_AKITA_PORT = 'JAPAN_AKITA_PORT'
    JAPAN_YOKOHAMA_PORT = 'JAPAN_YOKOHAMA_PORT'
    JAPAN_KOBE_PORT = 'JAPAN_KOBE_PORT'
    JAPAN_NAGOYA_PORT = 'JAPAN_NAGOYA_PORT'
    SOUTH_KOREA_PUSAN_PORT = 'SOUTH_KOREA_PUSAN_PORT'
    SOUTH_KOREA_INCHON_PORT = 'SOUTH_KOREA_INCHON_PORT'
    RUSSIA_VLADIVOSTOK_PORT = 'RUSSIA_VLADIVOSTOK_PORT'
    RUSSIA_VOSTOCHNYI_PORT = 'RUSSIA_VOSTOCHNYI_PORT'
    BELARUS_BREST_BORDER = 'BELARUS_BREST_BORDER'
    KAZAKHSTAN_DOSTIK_BORDER = 'KAZAKHSTAN_DOSTIK_BORDER'
    UZBEKISTAN_ALTUNKUL_BORDER = 'UZBEKISTAN_ALTUNKUL_BORDER'
    RUSSIA_NAUSHKI_BORDER = 'RUSSIA_NAUSHKI_BORDER'
    RUSSIA_ZABAIKALSK_BORDER = 'RUSSIA_ZABAIKALSK_BORDER'
    FAKE_INDIA_MUMBAI_PORT = 'FAKE_INDIA_MUMBAI_PORT'
    FAKE_IRAN_BENDER_ABBAS_PORT = 'FAKE_IRAN_BENDER_ABBAS_PORT'
    FAKE_GEORGIA_POTI_PORT = 'FAKE_GEORGIA_POTI_PORT'
    FAKE_ROMANIA_CONSTANCA_PORT = 'FAKE_ROMANIA_CONSTANCA_PORT'
    FAKE_BULGAR_BURGAS_PORT = 'FAKE_BULGAR_BURGAS_PORT'
    FAKE_RUSSIA_KALININGRAD_PORT = 'FAKE_RUSSIA_KALININGRAD_PORT'
    FAKE_RUSSIA_SPB_PORT = 'FAKE_RUSSIA_SPB_PORT'
    FAKE_RUSSIA_ARCHANGELSK_PORT = 'FAKE_RUSSIA_ARCHANGELSK_PORT'
    FAKE_RUSSIA_PETROPAVLIK_PORT = 'FAKE_RUSSIA_PETROPAVLIK_PORT'
    FAKE_EGYPT_ALEKSANDIA_PORT = 'FAKE_EGYPT_ALEKSANDIA_PORT'
    FAKE_FRANCE_MARSEL_PORT = 'FAKE_FRANCE_MARSEL_PORT'
    FAKE_GERMAN_GAMBURG_PORT = 'FAKE_GERMAN_GAMBURG_PORT'
    FAKE_NETHERLANDS_ROTERDAM_PORT = 'FAKE_NETHERLANDS_ROTERDAM_PORT'
    FAKE_RUSSIA_NOVOROSSISK_PORT = 'FAKE_RUSSIA_NOVOROSSISK_PORT'
    FAKE_RUSSIA_ASTRACHAN_PORT = 'FAKE_RUSSIA_ASTRACHAN_PORT'
    FAKE_BELARUS_MINSK_TERMINAL = 'FAKE_BELARUS_MINSK_TERMINAL'
    FAKE_RUSSIA_EKB_TERMINAL = 'FAKE_RUSSIA_EKB_TERMINAL'
    FAKE_RUSSIA_TOMSK_TERMINAL = 'FAKE_RUSSIA_TOMSK_TERMINAL'
    FAKE_RUSSIA_NOVOSIB_TERMINAL = 'FAKE_RUSSIA_NOVOSIB_TERMINAL'
    FAKE_RUSSIA_KRASNOYARSK_TERMINAL = 'FAKE_RUSSIA_KRASNOYARSK_TERMINAL'
    FAKE_RUSSIA_IRKUTSK_TERMINAL = 'FAKE_RUSSIA_IRKUTSK_TERMINAL'
    FAKE_RUSSIA_HABAROVSK_TERMINAL = 'FAKE_RUSSIA_HABAROVSK_TERMINAL'
    FAKE_RUSSIA_ORENBURG_TERMINAL = 'FAKE_RUSSIA_ORENBURG_TERMINAL'
    FAKE_RUSSIA_SAMARA_TERMINAL = 'FAKE_RUSSIA_SAMARA_TERMINAL'
    FAKE_RUSSIA_SARATOV_TERMINAL = 'FAKE_RUSSIA_SARATOV_TERMINAL'
    FAKE_RUSSIA_KAZAN_TERMINAL = 'FAKE_RUSSIA_KAZAN_TERMINAL'
    FAKE_RUSSIA_NIZNOVGOROD_TERMINAL = 'FAKE_RUSSIA_NIZNOVGOROD_TERMINAL'
    FAKE_RUSSIA_YAKUTSK_TERMINAL = 'FAKE_RUSSIA_YAKUTSK_TERMINAL'


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


class PR1ClassStep(str, enum.Enum):
    SELECT_LOGIST = 'SELECT_LOGIST'
    EXW_BUYER = 'EXW_BUYER'
    EXW_SELLER = 'EXW_SELLER'
    FCA_BUYER = 'FCA_BUYER'
    FCA_SELLER = 'FCA_SELLER'
    CPT_BUYER = 'CPT_BUYER'
    CPT_SELLER = 'CPT_SELLER'
    CIP_BUYER = 'CIP_BUYER'
    CIP_SELLER = 'CIP_SELLER'
    DAP_BUYER = 'DAP_BUYER'
    DAP_SELLER = 'DAP_SELLER'
    DPU_BUYER = 'DPU_BUYER'
    DPU_SELLER = 'DPU_SELLER'
    DDP_BUYER = 'DDP_BUYER'
    DDP_SELLER = 'DDP_SELLER'
    FAS_BUYER = 'FAS_BUYER'
    FAS_SELLER = 'FAS_SELLER'
    FOB_BUYER = 'FOB_BUYER'
    FOB_SELLER = 'FOB_SELLER'
    CFR_BUYER = 'CFR_BUYER'
    CFR_SELLER = 'CFR_SELLER'
    CIF_BUYER = 'CIF_BUYER'
    CIF_SELLER = 'CIF_SELLER'
    OPTIONS_COMPARISON = 'OPTIONS_COMPARISON'
    CONDITIONS_SELECTION = 'CONDITIONS_SELECTION'
    DESCRIBE_OPTION = 'DESCRIBE_OPTION'
    TEST_1 = 'TEST_1'
    TEST_2 = 'TEST_2'
    TEST_3 = 'TEST_3'
    TEST_4 = 'TEST_4'
    TEST_5 = 'TEST_5'
    TEST_6 = 'TEST_6'
    TEST_7 = 'TEST_7'
    TEST_8 = 'TEST_8'
    TEST_9 = 'TEST_9'
    TEST_10 = 'TEST_10'
    TEST_11 = 'TEST_11'
    TEST_12 = 'TEST_12'
    TEST_13 = 'TEST_13'
    TEST_14 = 'TEST_14'
    TEST_15 = 'TEST_15'
    TEST_16 = 'TEST_16'
    TEST_17 = 'TEST_17'
    TEST_18 = 'TEST_18'
    TEST_19 = 'TEST_19'
    TEST_20 = 'TEST_20'


class PR1ControlStep(str, enum.Enum):
    PR1_CONTROL_1 = 'PR1_CONTROL_1'
    PR1_CONTROL_2 = 'PR1_CONTROL_2'
    PR1_CONTROL_3 = 'PR1_CONTROL_3'
    TEST_1 = 'TEST_1'
    TEST_2 = 'TEST_2'
    TEST_3 = 'TEST_3'
    TEST_4 = 'TEST_4'
    TEST_5 = 'TEST_5'
    TEST_6 = 'TEST_6'
    TEST_7 = 'TEST_7'
    TEST_8 = 'TEST_8'
    TEST_9 = 'TEST_9'
    TEST_10 = 'TEST_10'


class PR2ClassStep(str, enum.Enum):
    SCREEN_1_INSTRUCTION_WITH_LEGEND = 'SCREEN_1_INSTRUCTION_WITH_LEGEND'
    SCREEN_2_TASK_DESCRIPTION = 'SCREEN_2_TASK_DESCRIPTION'
    SCREEN_3_SOURCE_DATA_FULL_ROUTES = 'SCREEN_3_SOURCE_DATA_FULL_ROUTES'
    SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME = 'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME'
    SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME = 'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME'
    SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER = 'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER'
    SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION = 'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION'
    SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY = 'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY'
    SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME = 'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME'
    SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME = 'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME'
    SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER = 'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER'
    SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION = 'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION'
    SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY = 'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY'
    SCREEN_5_DESCRIBE_CONTAINER_SELECTION = 'SCREEN_5_DESCRIBE_CONTAINER_SELECTION'
    SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_1 = 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_1'
    SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_2 = 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_2'
    SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_3 = 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_3'
    SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_4 = 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_4'
    SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_5 = 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_5'
    SCREEN_7_SOURCE_DATA_CHOOSE_DESTINATIONS = 'SCREEN_7_SOURCE_DATA_CHOOSE_DESTINATIONS'
    SCREEN_7_SOURCE_DATA_CHOOSE_PORTS = 'SCREEN_7_SOURCE_DATA_CHOOSE_PORTS'
    SCREEN_7_SOURCE_DATA_CHOOSE_BORDER = 'SCREEN_7_SOURCE_DATA_CHOOSE_BORDER'
    SCREEN_8_MAP_ROUTE_1 = 'SCREEN_8_MAP_ROUTE_1'
    SCREEN_8_MAP_ROUTE_2 = 'SCREEN_8_MAP_ROUTE_2'
    SCREEN_8_MAP_ROUTE_3 = 'SCREEN_8_MAP_ROUTE_3'
    SCREEN_8_MAP_ROUTE_4 = 'SCREEN_8_MAP_ROUTE_4'
    SCREEN_8_MAP_ROUTE_5 = 'SCREEN_8_MAP_ROUTE_5'
    SCREEN_8_MAP_ROUTE_6 = 'SCREEN_8_MAP_ROUTE_6'
    SCREEN_8_MAP_ROUTE_7 = 'SCREEN_8_MAP_ROUTE_7'
    SCREEN_8_MAP_ROUTE_8 = 'SCREEN_8_MAP_ROUTE_8'
    SCREEN_9_FORMED_ROUTES_TABLE = 'SCREEN_9_FORMED_ROUTES_TABLE'
    SCREEN_10_RISKS_1 = 'SCREEN_10_RISKS_1'
    SCREEN_10_RISKS_2 = 'SCREEN_10_RISKS_2'
    SCREEN_10_RISKS_3 = 'SCREEN_10_RISKS_3'
    SCREEN_10_RISKS_4 = 'SCREEN_10_RISKS_4'
    SCREEN_10_RISKS_TOTAL = 'SCREEN_10_RISKS_TOTAL'
    SCREEN_10_FULL_ROUTES_WITH_PLS = 'SCREEN_10_FULL_ROUTES_WITH_PLS'
    SCREEN_11_OPTIMAL_RESULTS_3PL1 = 'SCREEN_11_OPTIMAL_RESULTS_3PL1'
    SCREEN_11_OPTIMAL_RESULTS_3PL2 = 'SCREEN_11_OPTIMAL_RESULTS_3PL2'
    SCREEN_11_OPTIMAL_RESULTS_3PL3 = 'SCREEN_11_OPTIMAL_RESULTS_3PL3'
    SCREEN_11_OPTIMAL_RESULTS_COMBO = 'SCREEN_11_OPTIMAL_RESULTS_COMBO'
    SCREEN_13_CHOOSE_LOGIST = 'SCREEN_13_CHOOSE_LOGIST'


class WSCommandTypes(str, enum.Enum):
    INVITE_STUDENT = 'INVITE_STUDENT'
    SELECT_TYPE = 'SELECT_TYPE'
    START = 'START'
    RAISE_HAND = 'RAISE_HAND'
    FINISH = 'FINISH'
    EXIT = 'EXIT'


class EventType(str, enum.Enum):
    PR1 = 'PR1'
    PR2 = 'PR2'
    # CONTROL = 'CONTROL'


class EventMode(str, enum.Enum):
    CLASS = 'CLASS'
    CONTROL = 'CONTROL'
    # WORKOUT = 'WORKOUT'


class SelectLogist(BaseModel):
    computer_id: int
    event_id: str
    logist_index: Annotated[int, Field(strict=True, ge=0, lt=3)]


class GeneralStep(BaseModel):
    id: int
    name: str


class EventStatus(str, enum.Enum):
    NOT_STARTED = 'NOT_STARTED'
    STARTED = 'STARTED'
    FINISHED = 'FINISHED'


class StartEventResponse(BaseModel):
    event_id: str


class UserBase(BaseModel):
    first_name: constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')
    last_name: constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')
    surname: Optional[constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')] = None

    student_id: str
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class MiniUser(UserBase):
    id: str
    group_name: str
    group_id: str
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class ConnectedComputerUpdate(BaseModel):
    id: int
    users_ids: Optional[list[str]] = None
    event_id: Optional[str] = None
    event_type: Optional[EventType] = None
    event_mode: Optional[EventMode] = None
    is_connected: Optional[bool] = None
    step_code: Optional[str] = None
    help_requested: Optional[bool] = None
    is_searching_someone: Optional[bool] = None

    last_action: float = Field(default_factory=time.time)


class ConnectedComputer(BaseModel):
    id: int
    users_ids: list[str]
    event_id: Optional[str] = None
    event_type: Optional[EventType] = None
    event_mode: Optional[EventMode] = None
    is_connected: Optional[bool] = None
    step_code: Optional[str] = None
    help_requested: bool = False
    is_searching_someone: bool = False
    last_action: float = Field(default_factory=time.time)
    last_pong: float = Field(default_factory=time.time)

    def is_expired(self, expire_min: int = 12) -> bool:
        return (time.time() - self.last_action) > (expire_min * 60)

    def update_last_time(self):
        self.last_action = time.time()


class ConnectedComputerFrontResponse(BaseModel):
    id: int
    users: list[MiniUser]
    event_id: Optional[str] = None
    event_type: Optional[EventType] = None
    event_mode: Optional[EventMode] = None
    is_connected: Optional[bool] = False
    step_code: Optional[str] = None
    percentage: int = 0
    is_searching_someone: bool = False
    help_requested: bool = False


class ActualizeComputerPayload(BaseModel):
    event_type: EventType
    event_mode: EventMode


class ConnectedComputerEdit(BaseModel):
    id: int
    users_ids: Optional[list[str]] = None
    event_type: Optional[EventType] = None
    event_mode: Optional[EventMode] = None
    step: Optional[GeneralStep] = None
    is_connected: Optional[bool] = None
    is_searching_someone: Optional[bool] = None
    status: Optional[EventStatus] = None


class WSMessage(BaseModel):
    type: WSCommandTypes
    payload: Optional[Any] = None


class UserRole(str, enum.Enum):
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'


class Lesson(BaseModel):
    id: Optional[str] = None
    group_id: str
    group_name: str
    event_mode: Optional[EventMode] = None
    event_type: Optional[EventType] = None
    created_at: datetime = datetime.now()


class ForgotPasswordBody(BaseModel):
    username: str
    student_id: str


class ForgotPasswordResponse(BaseModel):
    username: str
    new_password: str


class UserCreateBody(UserBase):
    password: constr(min_length=8, max_length=35)
    group_id: str


class RequestEditsBody(BaseModel):
    user_id: str
    first_name: Optional[bool] = False
    last_name: Optional[bool] = False
    surname: Optional[bool] = False
    student_id: Optional[bool] = False
    group_id: Optional[bool] = False


class CheckApprovalResponse(BaseModel):
    is_approved: bool
    fields_to_be_fixed: Optional[list[str]] = Field(default_factory=list)


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
    history: list[UserEventHistory] = Field(default_factory=list)
    incoterms: dict[Incoterm, int] = Field(default_factory=dict)
    fix_for_approve_fields: Optional[list[str]] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class FullUser(UserCreateDB):
    id: str
    approved: bool
    fix_for_approve_fields: Optional[list[str]] = None


class TestCorrectsAndErrors(BaseModel):
    correct: int
    error: int


class PR2Risk(BaseModel):
    text: str
    id: int


class RisksWithRouteName(BaseModel):
    route_name: str
    risks: list[PR2Risk]


class UserHistoryElement(BaseModel):
    id: str
    type: EventType
    mode: EventMode
    created_at: datetime
    finished_at: datetime
    incoterms: Optional[dict[Incoterm, CorrectOrError]] = Field(default_factory=dict)
    incoterms_v2: Optional[dict[Incoterm, AnswerStatus]] = Field(default_factory=dict)
    incoterm_points_mapping: Optional[dict[Incoterm, int]] = Field(default_factory=dict)
    test: Optional[TestCorrectsAndErrors] = None
    description: Optional[str] = None
    errors: Optional[int] = None
    points: Optional[int] = None
    container_selection_explanation: Optional[str]
    delivery_option_explanation: Optional[str]
    risks_chosen_by_user: list[RisksWithRouteName] = Field(default_factory=list)


class UserOut(UserBase):
    id: str
    first_name: str
    last_name: str
    username: str
    surname: Optional[str] = None
    approved: bool = False
    group_name: Optional[str] = None
    group_id: Optional[str] = None
    role: UserRole = UserRole.STUDENT.value
    incoterms: Optional[dict[Incoterm, int]] = Field(default_factory=dict)
    fix_for_approve_fields: Optional[list[str]] = None
    history: list[UserHistoryElement] = Field(default_factory=list)


class UserEvent(BaseModel):
    event_type: EventType
    event_mode: EventMode
    points: int
    lesson_id: str
    created_at: datetime = datetime.now()


class UserOutWithEvents(UserOut):
    events_history: Optional[list[UserEvent]] = Field(default_factory=list)


class UserSearch(BaseModel):
    search: Optional[str] = None
    group_id: Optional[str] = None


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
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class GroupCreate(GroupBase):
    pass


class SearchPartner(BaseModel):
    computer_id: int


class InvitePartner(BaseModel):
    computer_id: int
    partner_computer_id: int


class AcceptInvite(BaseModel):
    computer_id: int
    partner_computer_id: int


class RejectInvite(BaseModel):
    computer_id: int
    partner_computer_id: int


class GroupOut(GroupBase):
    id: str
    is_hidden: Optional[bool] = False


class EventCheckpoint(BaseModel):
    step_id: int
    user_ids: list[str]
    points: int
    fails: int


class EventResult(UserBase):
    group_name: str
    username: str
    fails: int
    points: int


class EventStepResult(BaseModel):
    test_index: Optional[int] = 0
    step_code: str
    users_ids: list[str]
    fails: int
    incoterm: Optional[Incoterm]
    description: Optional[str] = None
    is_finished: bool = False
    comments: Optional[str] = None


class StepRole(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ALL = 'ALL'


class Step(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    role: Optional[StepRole] = None


class SubResult(BaseModel):
    correct: int = 0
    correct_with_fails: int = 0
    failed: int = 0


class PR2ClassResult(BaseModel):
    name: str
    last_name: str
    surname: Optional[str]
    group_name: str
    errors: int
    points: int


class PR1ControlResults(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    event_type: EventType
    event_mode: EventMode
    surname: Optional[str] = None
    event_id: str
    right_test_answers: int
    incoterms_points: dict[Incoterm, int]


class PR1ClassResults(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    event_type: EventType
    event_mode: EventMode
    surname: Optional[str] = None
    event_id: str
    test_results: list[SubResult]
    best_test_result: SubResult
    last_test_result: SubResult
    incoterms_results: dict[Incoterm, SubResult]
    minimal_incoterms: dict[Incoterm, AnswerStatus]


class EventInfo(BaseModel):
    id: Optional[str] = None
    computer_id: int
    is_finished: bool = False
    event_type: EventType
    event_mode: EventMode
    created_at: datetime = datetime.now()
    finished_at: Optional[datetime] = None
    users_ids: list[str]
    steps_results: list[EventStepResult] = Field(default_factory=list)
    results: Optional[Union[PR1ControlResults, list[PR2ClassResult], list[PR1ClassResults], list[EventResult]]] = None
    current_step: Union[Step, str]
    test_results: Optional[list[list[EventStepResult]]] = Field(default_factory=lambda: [[], [], []])


class BetsRolePR1(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'


class BetInfoIncotermsRolePR1(BaseModel):
    buyer: list[Incoterm]
    seller: list[Incoterm]
    common: Optional[list[Incoterm]] = Field(default_factory=list)


class PracticeOneBet(BaseModel):
    id: int
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
    bets: list[PracticeOneBetOut]


class BodyText(BaseModel):
    type: TextType
    texts: list[str]


class Logist(BaseModel):
    letter: str
    types: list[str]
    texts: list[str]
    # header: str
    # body: str


class OptionPR1(BaseModel):
    buyer: int
    seller: int
    total: int
    incoterm: Incoterm


class QuestionOption(BaseModel):
    id: int
    value: str
    is_correct: bool = False


class TestQuestionPR1(BaseModel):
    id: int
    question: str
    multiple_options: Optional[bool] = False
    right_ids: Optional[list[int]] = Field(default_factory=list)
    options: list[QuestionOption]
    incoterm: Optional[Incoterm] = None


class PR1ClassVariables(BaseModel):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    bets: list[PracticeOneBet]
    logists: Optional[list[Logist]]
    tests: list[list[TestQuestionPR1]]
    zero_step: Step


# class PR1ControlInputVariables(BaseModel):
#     product_price: int
#     total_products: int
#     packaging: int
#     product_examination: int
#     loading_during_transport: int
#     unloading_during_transport: int
#     main_delivery: int
#     export_customs_formalities_and_payments: int
#     delivery_to_port: int
#     loading_on_board: int
#     transport_to_destination: int
#     delivery_to_carrier: int
#     insurance: int
#     # Расходы на разгрузку, которые по договору перевозки относятся к продавцу
#     unloading_seller_agreement: int
#     import_customs_formalities_and_payments: int
#     transport_to_terminal: int
#     unloading_on_terminal: int


# class PR1ControlInput(BaseModel):
#     legend: str
#     to_point: str
#     from_point: str
#     product_name: str
#     variables: PR1ControlInputVariables


# class PR1ControlEvent(EventInfo, PR1ControlInput):
#     incoterms: list[Incoterm]
#     answers: dict[Incoterm, int]
#     event_mode = EventMode.CONTROL
#     event_type = EventType.PR1


# class PR1ControlEvent(EventInfo):
#     legend: str
#     test: Optional[list[TestQuestionPR1]]
#     incoterms: list[Incoterm]
#     product_price: int
#     product_quantity: Optional[int] = 0
#     packaging: Optional[int] = 0
#     product_check: Optional[int] = 0
#     loading_expenses: Optional[int] = 0
#     delivery_to_main_carrier: Optional[int] = 0
#     export_formalities: Optional[int] = 0
#     loading_unloading_to_point: Optional[int] = 0
#     delivery_to_unloading_port: Optional[int] = 0
#     loading_on_board: Optional[int] = 0
#     transport_expenses_to_port: Optional[int] = 0
#     products_insurance: Optional[int] = 0
#     unloading_on_seller: Optional[int] = 0
#     import_formalities: Optional[int] = 0
#     unloading_on_terminal: Optional[int] = 0
#
#     def get_formula_with_nums(self, incoterm: str) -> str:
#         if incoterm == Incoterm.EXW.value:
#             nums = [self.product_price, self.packaging, self.product_check]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.FCA:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_expenses,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.FOB.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_unloading_to_point,
#                 self.delivery_to_unloading_port,
#                 self.export_formalities,
#                 self.loading_on_board,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.FAS.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_unloading_to_point,
#                 self.delivery_to_unloading_port,
#                 self.export_formalities,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.CFR.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_unloading_to_point,
#                 self.delivery_to_unloading_port,
#                 self.export_formalities,
#                 self.loading_on_board,
#                 self.transport_expenses_to_port,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.CIP.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_expenses,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#                 self.transport_expenses_to_port,
#                 self.products_insurance,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.CPT.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_expenses,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#                 self.transport_expenses_to_port,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.CIF.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_unloading_to_point,
#                 self.delivery_to_unloading_port,
#                 self.export_formalities,
#                 self.loading_on_board,
#                 self.transport_expenses_to_port,
#                 self.products_insurance,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.DDP.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_expenses,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#                 self.transport_expenses_to_port,
#                 self.unloading_on_seller,
#                 self.import_formalities,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.DAP.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#                 self.transport_expenses_to_port,
#                 self.unloading_on_seller,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#         elif incoterm == Incoterm.DPU.value:
#             nums = [
#                 self.product_price,
#                 self.packaging,
#                 self.product_check,
#                 self.loading_expenses,
#                 self.delivery_to_main_carrier,
#                 self.export_formalities,
#                 self.transport_expenses_to_port,
#                 self.unloading_on_terminal,
#             ]
#             nums = [str(num) for num in nums if num != 0]
#             pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
#             return pre + ' + '.join(nums)
#
#     def get_formula(self, incoterm: str):
#         formula_by_incoterm = {
#             'EXW': 'КС = Цена производителя + Упаковка + Проверка товара',
#             'FCA': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара основному перевозчику + Экспортные таможенные формальности и платежи',
#             'FOB': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна',
#             'FAS': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи',
#             'CFR': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна + Транспортные расходы до порта назначения',
#             'CIP': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на страхование груза',
#             'CPT': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения',
#             'CIF': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна + Транспортные расходы до порта назначения + Расходы на страхование груза',
#             'DDP': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на разгрузку, которые по договору перевозки относятся к продавцу + Импортные таможенные формальности и платежи',
#             'DAP': 'КС = Цена производителя + Упаковка + Проверка товара + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на разгрузку, которые по договору перевозки относятся к продавцу',
#             'DPU': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до терминала + Выгрузка товара на терминале',
#         }
#
#         return formula_by_incoterm[incoterm]
#
#     def calculate_incoterm(self, incoterm: str):
#         if incoterm == Incoterm.EXW.value:
#             return self.product_price * self.product_quantity + self.packaging + self.product_check
#         elif incoterm == Incoterm.FCA:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_expenses
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#             )
#         elif incoterm == Incoterm.FOB.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_unloading_to_point
#                 + self.delivery_to_unloading_port
#                 + self.export_formalities
#                 + self.loading_on_board
#             )
#         elif incoterm == Incoterm.FAS.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_unloading_to_point
#                 + self.delivery_to_unloading_port
#                 + self.export_formalities
#             )
#         elif incoterm == Incoterm.CFR.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_unloading_to_point
#                 + self.delivery_to_unloading_port
#                 + self.export_formalities
#                 + self.loading_on_board
#                 + self.transport_expenses_to_port
#             )
#         elif incoterm == Incoterm.CIP.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_expenses
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#                 + self.transport_expenses_to_port
#                 + self.products_insurance
#             )
#         elif incoterm == Incoterm.CPT.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_expenses
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#                 + self.transport_expenses_to_port
#             )
#         elif incoterm == Incoterm.CIF.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_unloading_to_point
#                 + self.delivery_to_unloading_port
#                 + self.export_formalities
#                 + self.loading_on_board
#                 + self.transport_expenses_to_port
#                 + self.products_insurance
#             )
#         elif incoterm == Incoterm.DDP.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_expenses
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#                 + self.transport_expenses_to_port
#                 + self.unloading_on_seller
#                 + self.import_formalities
#             )
#         elif incoterm == Incoterm.DAP.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#                 + self.transport_expenses_to_port
#                 + self.unloading_on_seller
#             )
#         elif incoterm == Incoterm.DPU.value:
#             return (
#                 self.product_price * self.product_quantity
#                 + self.packaging
#                 + self.product_check
#                 + self.loading_expenses
#                 + self.delivery_to_main_carrier
#                 + self.export_formalities
#                 + self.transport_expenses_to_port
#                 + self.unloading_on_terminal
#             )


class PracticeOneVariant(EventInfo):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    tables: dict[BetsRolePR1, list[TablePR1]]
    logists: list[Logist]
    options: list[OptionPR1]
    tests: list[list[TestQuestionPR1]]


class ExamStep(BaseModel):
    id: int
    code: str
    name: str


class BetInfoValuePR1(BaseModel):
    min: int
    max: int


class BetInfoPR1(BaseModel):
    id: int
    name: str
    value_percentage: BetInfoValuePR1
    incoterms: BetInfoIncotermsRolePR1


class ClassicTestQuestionBlock(BaseModel):
    first_block: list[TestQuestionPR1]
    second_block: list[TestQuestionPR1]
    third_block: list[TestQuestionPR1]


class PR1ClassInfo(BaseModel):
    legend_pattern: str
    all_incoterms: list[str]
    steps: list[Step]
    # exam_steps: list[ExamStep]
    bets: list[BetInfoPR1]
    logists: list[Logist]
    classic_test_questions: ClassicTestQuestionBlock
    # control_test_questions: list[TestQuestionPR1]
    hints: dict[Incoterm, str]


class PR2Point(BaseModel):
    code: str
    country: str
    city: str
    type: str
    is_fake: bool


class PR2ClassInfo(BaseModel):
    legend: str
    explanation: str
    steps_codes: list[str]
    all_points: list[PR2Point]
    all_risks: list[list[PR2Risk]]


class PR1ControlInfo(BaseModel):
    legends: list[str]
    random_incoterms: list[list[Incoterm]]
    test_questions: list[TestQuestionPR1]


class UserCredentials(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')] = None
    last_name: Optional[constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')] = None
    surname: Optional[constr(min_length=2, max_length=35, regex=r'^[а-яА-ЯёЁ \-–—]+$')] = None

    student_id: Optional[str] = None
    group_id: Optional[str] = None


class ResponseMessage(BaseModel):
    message: str


class ChangePasswordBody(BaseModel):
    last_name: str
    student_id: str
    new_password: str


class UserToApprove(BaseModel):
    id: str
    first_name: str
    last_name: str
    surname: Optional[str] = None
    group_name: str
    student_id: Optional[str] = None


# class TestCorrectsAndErrors(BaseModel):
#     correct: int
#     error: int


# class UserHistoryElement(BaseModel):
#     id: str
#     type: EventType
#     mode: EventMode
#     created_at: datetime
#     finished_at: datetime
#     incoterms: Optional[dict[Incoterm, CorrectOrError]] = {}
#     incoterm_points_mapping: Optional[dict[Incoterm, int]] = {}
#     test: Optional[TestCorrectsAndErrors] = None
#     description: Optional[str] = None
#     errors: Optional[int] = None
#     points: Optional[int] = None


class GetUserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    surname: Optional[str] = None
    username: str
    group_id: str
    group_name: str
    history: list[UserHistoryElement] = Field(default_factory=list)


class UserChangePassword(BaseModel):
    password: str


class SourceDataChooseScreen(BaseModel):
    departure_points_codes: list[str]
    destination_points_codes: list[str]
    ports_points_codes: list[str]
    borders_points_codes: list[str]


class CheckpointData(BaseModel):
    computer_id: int
    event_id: str
    step_code: Union[PR1ClassStep, PR1ControlStep, PR2ClassStep]
    text: Optional[str]
    answer_ids: Optional[list[int]] = Field(default_factory=list)
    chosen_index: Optional[int]
    chosen_incoterm: Optional[Incoterm]
    chosen_letter: Optional[str] = None
    formula: Optional[str]
    formulas: Optional[list[str]]
    destination_points_codes: Optional[list[str]]
    route_points_codes: Optional[list[str]]
    ports_codes: Optional[list[str]]
    borders_codes: Optional[list[str]]
    right_risks_codes: Optional[list[str]]
    risk_ids_desc: Optional[list[int]]


class JoinData(BaseModel):
    computer_id: conint(ge=0)
    user_id: conint(ge=0)


class StartEventComputer(BaseModel):
    computer_id: int
    type: int
    mode: EventMode


class StartEventDto(BaseModel):
    computer_id: int
    type: EventType
    mode: EventMode


class PR1ClassChosenBet(BaseModel):
    id: int
    name: str
    rate: float
    chosen_by: BetsRolePR1
    type: PR1ClassBetType


class IncotermInfo(BaseModel):
    bets: list[PR1ClassChosenBet]
    agreement_price_seller: int
    delivery_price_buyer: int
    total: int


class IncotermInfoSummarize(BaseModel):
    agreement_price_seller: int
    delivery_price_buyer: int
    total: int


class ChosenOption(IncotermInfoSummarize):
    incoterm: Incoterm


class PR1ClassEvent(EventInfo):
    legend: str
    logists: list[Logist]
    chosen_logist_letter: Optional[str] = None
    product: str
    from_country: str
    to_country: str
    product_price: int
    bets: list[PracticeOneBet]
    test_index: int = 0
    common_bets_ids_chosen_by_seller: Optional[dict[str, list[int]]] = Field(default_factory=dict)
    describe_option: Optional[str] = None
    options_comparison: Optional[dict[Incoterm, IncotermInfo]]
    chosen_option: Optional[ChosenOption]
    tests: Optional[list[list[TestQuestionPR1]]]
    test_results: Optional[list[list[EventStepResult]]] = Field(default_factory=lambda: [[], [], []])
    results: Optional[list[PR1ClassResults]] = Field(default_factory=list)


class PackageSize(BaseModel):
    length: float
    width: float
    height: float


class BestPL(BaseModel):
    index: int
    value: int


class MiniRoute(BaseModel):
    from_country: str
    to_country: str
    weight_in_ton: int
    best_pls: list[BestPL]
    tons: int
    n_40_foot_containers: int


class FullRoute(BaseModel):
    through: str
    country_from: str
    weight_in_tons: int
    country_to: str
    points: list[PR2Point]
    three_pls_bets: list[Optional[int]]


class PR2SourceData(BaseModel):
    mini_routes: list[MiniRoute]
    full_routes: list[FullRoute]
    package_size: PackageSize
    package_weight_in_ton: float
    transport_package_volume: float
    number_of_packages_in_20_foot_container: int
    number_of_packages_in_40_foot_container: int
    loading_volume_20_foot_container: float
    loading_volume_40_foot_container: float
    all_points: list[PR2Point]
    departure_points_strs: list[str]
    destination_points_codes: list[str]
    ports_points_codes: list[str]
    borders_points_codes: list[str]
    terminals_points_codes: list[str]


class PR2ClassEvent(EventInfo):
    legend: str
    explanation: str
    source_data: PR2SourceData
    container_selection_explanation: Optional[str]
    delivery_option_explanation: Optional[str]
    risks_chosen_by_user: list[RisksWithRouteName] = Field(default_factory=list)


class PR2ControlInfo(BaseModel):
    legends: list[str]
    random_incoterms: list[list[Incoterm]]


class PR1ControlStepVariant(BaseModel, ABC):
    incoterm: Incoterm

    @classmethod
    @abstractmethod
    def create(cls):
        pass

    @abstractmethod
    def get_formula_with_nums(self) -> str:
        pass

    @abstractmethod
    def calculate(self) -> int:
        pass

    @abstractmethod
    def get_formatted_legend(self) -> int:
        pass


class PR1ControlStep1(PR1ControlStepVariant):
    price_for_each: int  # 5-50 (step 5)
    quantity: int  # 5000-9000 (step 100)
    transport_package_price: int  # price_for_each * quantity / 100
    delivery_to_port: int  # 1000-5000 (step 100)
    loading_unloading_expenses: int  # delivery_to_port * 0.1
    sea_delivery_to_destination: int  # 9000-12000 (step 100)
    loading_on_destination: int  # sea_delivery_to_destination * 0.05
    insurance: int  # price_for_each * quantity * 0.02
    export_formal_payments: int  # price_for_each * quantity * 0.15
    incoterm: Incoterm  # FOB, CFR, CIF, FAS

    @classmethod
    def create(cls):
        from constants.pr1_control_info import pr1_control_info

        price_for_each = random.randrange(5, 56, 5)
        quantity = random.randrange(5000, 9001, 100)
        transport_package_price = price_for_each * quantity / 100
        delivery_to_port = random.randrange(1000, 5001, 100)
        loading_unloading_expenses = delivery_to_port * 0.1
        sea_delivery_to_destination = random.randrange(9000, 12001, 100)
        loading_on_destination = sea_delivery_to_destination * 0.05
        insurance = price_for_each * quantity * 0.02
        export_formal_payments = price_for_each * quantity * 0.15
        incoterm = random.choice(pr1_control_info.random_incoterms[0])

        return cls(
            price_for_each=price_for_each,
            quantity=quantity,
            transport_package_price=int(transport_package_price),
            delivery_to_port=delivery_to_port,
            loading_unloading_expenses=int(loading_unloading_expenses),
            sea_delivery_to_destination=sea_delivery_to_destination,
            loading_on_destination=int(loading_on_destination),
            insurance=int(insurance),
            export_formal_payments=int(export_formal_payments),
            incoterm=incoterm,
        )

    def get_formatted_legend(self) -> int:
        from constants.pr1_control_info import pr1_control_info

        return pr1_control_info.legends[0].format(
            self.price_for_each,
            self.quantity,
            self.transport_package_price,
            self.delivery_to_port,
            self.loading_unloading_expenses,
            self.sea_delivery_to_destination,
            self.loading_on_destination,
            self.insurance,
            self.export_formal_payments,
            {
                Incoterm.FAS: 'FAS порт отправления',  # TODO: А где он?
                Incoterm.FOB: 'FOB порт отправления',
                Incoterm.CFR: 'CFR порт назначения',
                Incoterm.CIF: 'CIF порт назначения',
            }[self.incoterm],
        )

    def get_formula_with_nums(self) -> str:
        if self.incoterm == Incoterm.FOB.value:
            nums = [
                self.price_for_each,
                self.transport_package_price,
                self.delivery_to_port,
                self.loading_unloading_expenses,
                self.export_formal_payments,
                self.loading_on_destination,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.CFR.value:
            nums = [
                self.price_for_each,
                self.transport_package_price,
                self.loading_unloading_expenses,
                self.sea_delivery_to_destination,
                self.delivery_to_port,
                self.export_formal_payments,
                self.loading_on_destination,
                self.insurance,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.CIF.value:
            nums = [
                self.price_for_each,
                self.transport_package_price,
                self.loading_unloading_expenses,
                self.delivery_to_port,
                self.sea_delivery_to_destination,
                self.loading_on_destination,
                self.export_formal_payments,
                self.insurance,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.FAS.value:
            nums = [
                self.price_for_each,
                self.transport_package_price,
                self.loading_unloading_expenses,
                self.delivery_to_port,
                self.export_formal_payments,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)

    def calculate(self) -> int:
        if self.incoterm == Incoterm.FOB.value:
            return (
                self.price_for_each * self.quantity
                + self.transport_package_price
                + self.loading_unloading_expenses
                + self.delivery_to_port
                + self.export_formal_payments
                + self.loading_on_destination
            )
        elif self.incoterm == Incoterm.CFR.value:
            return (
                self.price_for_each * self.quantity
                + self.transport_package_price
                + self.loading_unloading_expenses
                + self.sea_delivery_to_destination
                + self.delivery_to_port
                + self.export_formal_payments
                + self.loading_on_destination
                + self.insurance
            )
        elif self.incoterm == Incoterm.CIF.value:
            return (
                self.price_for_each * self.quantity
                + self.transport_package_price
                + self.loading_unloading_expenses
                + self.delivery_to_port
                + self.loading_on_destination
                + self.sea_delivery_to_destination
                + self.export_formal_payments
                + self.insurance
            )
        elif self.incoterm == Incoterm.FAS.value:
            return (
                self.price_for_each * self.quantity
                + self.transport_package_price
                + self.loading_unloading_expenses
                + self.delivery_to_port
                + self.export_formal_payments
            )


class PR1ControlStep2(PR1ControlStepVariant):
    price_for_each: int  # 150-500 (step 50)
    quantity: int  # 2500-8000 (step 500)
    export_formal_payments: int  # price_for_each * quantity * 0.15
    insurance: int  # price_for_each * quantity * 0.02
    delivery_to_port: int  # 9000-15000 (step 100)
    delivery_from_port_to_terminal: int  # 1500-3500 (step 100)
    incoterm: Incoterm  # FCA, CIP, CPT

    def get_formatted_legend(self) -> int:
        from constants.pr1_control_info import pr1_control_info

        return pr1_control_info.legends[1].format(
            self.quantity,
            self.price_for_each,
            self.export_formal_payments,
            self.insurance,
            self.delivery_to_port,
            self.delivery_from_port_to_terminal,
            {
                Incoterm.FCA: 'FCA Калининград',
                Incoterm.CIP: 'CIP место назначения',
                Incoterm.CPT: 'CPT место назначения',
            }[self.incoterm],
        )

    @classmethod
    def create(cls):
        from constants.pr1_control_info import pr1_control_info

        price_for_each = random.randrange(150, 501, 50)
        quantity = random.randrange(2500, 8001, 500)
        export_formal_payments = price_for_each * quantity * 0.15
        insurance = price_for_each * quantity * 0.02
        delivery_to_port = random.randrange(9000, 15001, 100)
        delivery_from_port_to_terminal = random.randrange(1500, 3501, 100)
        incoterm = random.choice(pr1_control_info.random_incoterms[1])

        return cls(
            price_for_each=price_for_each,
            quantity=quantity,
            export_formal_payments=int(export_formal_payments),
            insurance=int(insurance),
            delivery_to_port=delivery_to_port,
            delivery_from_port_to_terminal=delivery_from_port_to_terminal,
            incoterm=incoterm,
        )

    def get_formula_with_nums(self) -> str:
        if self.incoterm == Incoterm.FCA.value:
            nums = [self.price_for_each, self.delivery_to_port, self.export_formal_payments]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.CIP.value:
            nums = [
                self.price_for_each,
                self.delivery_to_port,
                self.export_formal_payments,
                self.delivery_from_port_to_terminal,
                self.insurance,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.CPT.value:
            nums = [
                self.price_for_each,
                self.delivery_to_port,
                self.export_formal_payments,
                self.delivery_from_port_to_terminal,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)

    def calculate(self) -> int:
        if self.incoterm == Incoterm.FCA.value:
            return self.price_for_each * self.quantity + self.delivery_to_port + self.export_formal_payments
        elif self.incoterm == Incoterm.CIP.value:
            return (
                self.price_for_each * self.quantity
                + self.delivery_to_port
                + self.export_formal_payments
                + self.delivery_from_port_to_terminal
                + self.insurance
            )
        elif self.incoterm == Incoterm.CPT.value:
            return (
                self.price_for_each * self.quantity
                + self.delivery_to_port
                + self.export_formal_payments
                + self.delivery_from_port_to_terminal
            )


class PR1ControlStep3(PR1ControlStepVariant):
    quantity: int  # 100-900 (step 50)
    price_for_each: int  # 200-1000 (step 100)
    delivery_to_border: int  # 2000-3000 (step 100)
    territory_delivery: int  # delivery_to_border * 1.2
    export_formal_payments: int  # price_for_each * quantity * 0.15
    import_formal_payments: int  # price_for_each * quantity * 0.1
    incoterm: Incoterm  # EXW(в 5 раз реже!), DDP, DPU, DAP

    @classmethod
    def create(cls):
        from constants.pr1_control_info import pr1_control_info

        quantity = random.randrange(100, 901, 50)
        price_for_each = random.randrange(200, 1001, 100)
        delivery_to_border = random.randrange(2000, 3001, 100)
        territory_delivery = delivery_to_border * 1.2
        export_formal_payments = price_for_each * quantity * 0.15
        import_formal_payments = price_for_each * quantity * 0.1
        incoterm = random.choice(pr1_control_info.random_incoterms[2])

        return cls(
            quantity=quantity,
            price_for_each=price_for_each,
            delivery_to_border=delivery_to_border,
            territory_delivery=int(territory_delivery),
            export_formal_payments=int(export_formal_payments),
            import_formal_payments=int(import_formal_payments),
            incoterm=incoterm,
        )

    def get_formatted_legend(self) -> int:
        from constants.pr1_control_info import pr1_control_info

        return pr1_control_info.legends[2].format(
            self.quantity,
            self.price_for_each,
            self.delivery_to_border,
            self.territory_delivery,
            self.export_formal_payments,
            self.import_formal_payments,
            {
                Incoterm.EXW: 'EXW склад производителя',
                Incoterm.DDP: 'DDP место назначения',
                Incoterm.DPU: 'DPU место назначения',
                Incoterm.DAP: 'DAP место назначения'
            }[self.incoterm],
        )

    def get_formula_with_nums(self) -> str:
        if self.incoterm == Incoterm.EXW.value:
            nums = [self.price_for_each]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.DDP.value:
            nums = [
                self.price_for_each,
                self.delivery_to_border,
                self.export_formal_payments,
                self.territory_delivery,
                self.import_formal_payments,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.DPU.value:
            nums = [
                self.price_for_each,
                self.delivery_to_border,
                self.export_formal_payments,
                self.territory_delivery,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)
        elif self.incoterm == Incoterm.DAP.value:
            nums = [
                self.price_for_each,
                self.delivery_to_border,
                self.export_formal_payments,
                self.territory_delivery,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.quantity} * '
            return pre + ' + '.join(nums)

    def calculate(self) -> int:
        if self.incoterm == Incoterm.EXW.value:
            return self.price_for_each * self.quantity
        elif self.incoterm == Incoterm.DDP.value:
            return (
                self.price_for_each * self.quantity
                + self.delivery_to_border
                + self.export_formal_payments
                + self.territory_delivery
                + self.import_formal_payments
            )
        elif self.incoterm == Incoterm.DPU.value:
            return (
                self.price_for_each * self.quantity
                + self.delivery_to_border
                + self.export_formal_payments
                + self.territory_delivery
            )
        elif self.incoterm == Incoterm.DAP.value:
            return (
                self.price_for_each * self.quantity
                + self.delivery_to_border
                + self.export_formal_payments
                + self.territory_delivery
            )


class PR1ControlEvent(EventInfo):
    step1: PR1ControlStep1
    step2: PR1ControlStep2
    step3: PR1ControlStep3
    test: Optional[list[TestQuestionPR1]]


class FormulaRow(BaseModel):
    name: str
    formula: str


class ContainerResult(BaseModel):
    header: str
    rows: list[FormulaRow]


class PLRoute(BaseModel):
    supply_chain: str
    route_number: int
    through: str
    provider: str
    containers_num: int
    pl_bet: int
    delivery_price_formula: str
    full_route_index: int


class PLOption(BaseModel):
    name: str
    formula: str
    right_indexes: list[int]


class ButtonNumber(BaseModel):
    text: str
    value: Union[float, int]


class ContainerRoute(BaseModel):
    route: str
    weight_in_tons: int
    formulas: list[str]
    formula_with_answer: str


class MiniRouteHint(BaseModel):
    route: str
    tons: int
    n_40_containers_formula: str


class FullRouteHint(BaseModel):
    route: str
    through: str
    pls: list[Optional[int]]


class RouteWithRisk(BaseModel):
    name: str
    risks_with_route_name: RisksWithRouteName


class RoutePart(BaseModel):
    from_code: str
    to_code: str


class CurrentStepResponse(BaseModel):
    is_finished: bool = False
    current_step: Optional[Union[Step, str]]
    bets: Optional[list[PracticeOneBet]]
    options_comparison: Optional[dict[Incoterm, IncotermInfo]]
    delivery_options: Optional[dict[Incoterm, IncotermInfoSummarize]]
    test_question: Optional[TestQuestionPR1]
    logists: Optional[list[Logist]]
    product: Optional[str]
    from_country: Optional[str]
    to_country: Optional[str]
    product_price: Optional[int]
    legend: Optional[str]
    right_answer: Optional[float]
    right_formula: Optional[str]
    right_formula_with_nums: Optional[str]
    image_name: Optional[str]
    explanation: Optional[str]
    transport_package_info_text: Optional[str]
    screen_texts: Optional[list[str]]
    mini_routes: Optional[list[MiniRoute]]
    full_routes: Optional[list[FullRoute]]
    suggested_services: Optional[list[PR2Point]]
    container_foots: Optional[int]
    container_length: Optional[float]
    container_width: Optional[float]
    container_height: Optional[float]
    container_load_capacity: Optional[float]

    loading_volume: Optional[float]
    package_volume: Optional[float]
    number_of_packages_in_container: Optional[int]

    package_length: Optional[float]
    package_width: Optional[float]
    package_height: Optional[float]
    package_weight_in_ton: Optional[float]

    containers_results: Optional[list[ContainerResult]]

    points_codes_to_show: Optional[list[PR2PointsCodes]]

    start_point_code: Optional[PR2PointsCodes]
    end_point_code: Optional[PR2PointsCodes]
    route_length: Optional[int]
    right_route_codes: Optional[list[PR2PointsCodes]]

    current_route: Optional[FullRoute]
    risks: Optional[list[PR2Risk]]

    pl_routes: Optional[list[list[PLRoute]]]

    pl_options: Optional[list[PLOption]]

    pl1_formula: Optional[str]
    pl2_formula: Optional[str]
    pl3_formula: Optional[str]
    combo_formula: Optional[str]

    pl1_risks: Optional[list[PR2Risk]]
    pl2_risks: Optional[list[PR2Risk]]
    pl3_risks: Optional[list[PR2Risk]]
    combo_risks: Optional[list[PR2Risk]]

    container_routes_with_formulas: Optional[list[ContainerRoute]]

    extra_button_numbers: Optional[list[ButtonNumber]]

    number_of_packages_in_20_foot_container: Optional[int]
    number_of_packages_in_40_foot_container: Optional[int]

    all_points: Optional[list[PR2Point]]
    departure_points_strs: Optional[list[str]]
    destination_points_codes: Optional[list[str]]
    ports_points_codes: Optional[list[str]]
    borders_points_codes: Optional[list[str]]
    terminals_points_codes: Optional[list[str]]

    mini_routes_hints: Optional[list[list[MiniRouteHint]]]
    full_routes_hints: Optional[list[list[FullRouteHint]]]

    routes_with_risks: Optional[list[RouteWithRisk]]

    risks_chosen_by_user: Optional[list[RisksWithRouteName]]

    route_parts: Optional[list[RoutePart]]

    incoterm: Optional[Incoterm]


class CheckpointResponse(BaseModel):
    status: Optional[str] = None
    next_step: Optional[Union[Step, str]] = None
    fails: Optional[int] = 0
    missed_ids: Optional[list[int]] = Field(default_factory=list)
    not_needed_ids: Optional[list[int]] = Field(default_factory=list)
    hint: Optional[str]


# if __name__ == '__main__':
#     for incoterm in (Incoterm.FOB, Incoterm.CFR, Incoterm.CIF, Incoterm.FAS):
#         pr1_inc = PR1ControlStep1.create(incoterm)
#         print(f'Инкотерм: {incoterm}\n')
#         print(f'Легенда:')
#         print(pr1_inc.get_formatted_legend())
#         print(f'Формула: {pr1_inc.get_formula_with_nums()} = {pr1_inc.calculate()}')
#         print('\n\n')
#
#     # FCA, CIP, CPT
#     for incoterm in (Incoterm.FCA, Incoterm.CIP, Incoterm.CPT):
#         pr1_inc = PR1ControlStep2.create(incoterm)
#         print(f'Инкотерм: {incoterm}\n')
#         print(f'Легенда:')
#         print(pr1_inc.get_formatted_legend())
#         print(f'Формула: {pr1_inc.get_formula_with_nums()} = {pr1_inc.calculate()}')
#         print('\n\n')
#
#     # EXW(в 5 раз реже!), DDP, DPU
#     for incoterm in (Incoterm.EXW, Incoterm.DDP, Incoterm.DPU):
#         pr1_inc = PR1ControlStep3.create(incoterm)
#         print(f'Инкотерм: {incoterm}\n')
#         print(f'Легенда:')
#         print(pr1_inc.get_formatted_legend())
#         print(f'Формула: {pr1_inc.get_formula_with_nums()} = {pr1_inc.calculate()}')
#         print('\n\n')
