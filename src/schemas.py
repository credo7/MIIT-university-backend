import enum
from datetime import datetime
from typing import Optional, Union, Any
from bson import ObjectId

from typing_extensions import Annotated
from pydantic import BaseModel, constr, conint, Field
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


class AnswerStatus(str, enum.Enum):
    CORRECT = 'CORRECT'
    CORRECT_WITH_FAILS = 'CORRECT_WITH_FAILS'
    FAILED = 'FAILED'


class TextType(str, enum.Enum):
    text = 'text'
    dash = 'dash'
    enumerated = 'enumerated'


class PR1ClassBetType(str, enum.Enum):
    COMMON = 'COMMON'
    BUYER = 'BUYER'
    SELLER = 'SELLER'


class CheckpointResponseStatus(str, enum.Enum):
    SUCCESS = 'SUCCESS'
    TRY_AGAIN = 'TRY_AGAIN'
    FAILED = 'FAILED'


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
    INCOTERM_EXW = 'INCOTERM_EXW'
    INCOTERM_FCA = 'INCOTERM_FCA'
    INCOTERM_CPT = 'INCOTERM_CPT'
    INCOTERM_CIP = 'INCOTERM_CIP'
    INCOTERM_DAP = 'INCOTERM_DAP'
    INCOTERM_DPU = 'INCOTERM_DPU'
    INCOTERM_DDP = 'INCOTERM_DDP'
    INCOTERM_FAS = 'INCOTERM_FAS'
    INCOTERM_FOB = 'INCOTERM_FOB'
    INCOTERM_CFR = 'INCOTERM_CFR'
    INCOTERM_CIF = 'INCOTERM_CIF'
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


class ConnectedComputer(BaseModel):
    id: int
    users_ids: list[str]
    event_type: Optional[EventType] = None
    event_mode: Optional[EventMode] = None
    is_connected: Optional[bool] = False
    step: Optional[GeneralStep] = None
    is_searching_someone: bool = False


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


class UserBase(BaseModel):
    first_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    last_name: constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')
    surname: Optional[constr(min_length=2, max_length=35, regex='^[а-яА-ЯёЁ]+$')] = None


class UserCreateBody(UserBase):
    password: constr(min_length=8, max_length=35)
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
    history: list[UserEventHistory] = []


class FullUser(UserCreateDB):
    id: str
    approved: bool


class UserOut(UserBase):
    id: str
    first_name: str
    last_name: str
    surname: Optional[str] = None
    approved: bool = False
    group_name: Optional[str] = None
    group_id: Optional[str] = None
    role: UserRole = UserRole.STUDENT.value
    incoterms: dict[Incoterm, int] = {}


class UserEvent(BaseModel):
    event_type: EventType
    event_mode: EventMode
    points: int
    lesson_id: str
    created_at: datetime = datetime.now()


class UserOutWithEvents(UserOut):
    events_history: Optional[list[UserEvent]] = []


class UserSearch(BaseModel):
    search: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None


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


class StepRole(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'
    ALL = 'ALL'


class Step(BaseModel):
    id: int
    code: str
    name: str
    role: StepRole


class SubResult(BaseModel):
    correct: int = 0
    correct_with_fails: int = 0
    failed: int = 0


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
    steps_results: list[EventStepResult] = []
    results: list[EventResult] = []
    current_step: Union[Step, str]


class BetsRolePR1(str, enum.Enum):
    BUYER = 'BUYER'
    SELLER = 'SELLER'


class BetInfoIncotermsRolePR1(BaseModel):
    buyer: list[Incoterm]
    seller: list[Incoterm]
    common: Optional[list[Incoterm]] = []


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
    header: str
    body: list[BodyText]


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
    right_ids: Optional[list[int]] = []
    options: list[QuestionOption]
    incoterm: Optional[Incoterm] = None


class PR1ClassVariables(BaseModel):
    legend: str
    product: str
    from_country: str
    to_country: str
    product_price: int
    bets: list[PracticeOneBet]
    logists: list[Logist]
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


class PR1ControlEvent(EventInfo):
    legend: str
    test: Optional[list[TestQuestionPR1]]
    incoterms: list[Incoterm]
    product_price: int
    product_quantity: Optional[int] = 0
    packaging: Optional[int] = 0
    product_check: Optional[int] = 0
    loading_expenses: Optional[int] = 0
    delivery_to_main_carrier: Optional[int] = 0
    export_formalities: Optional[int] = 0
    loading_unloading_to_point: Optional[int] = 0
    delivery_to_unloading_port: Optional[int] = 0
    loading_on_board: Optional[int] = 0
    transport_expenses_to_port: Optional[int] = 0
    products_insurance: Optional[int] = 0
    unloading_on_seller: Optional[int] = 0
    import_formalities: Optional[int] = 0
    unloading_on_terminal: Optional[int] = 0

    def get_formula_with_nums(self, incoterm: str) -> str:
        if incoterm == Incoterm.EXW.value:
            nums = [self.product_price, self.packaging, self.product_check]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.FCA:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_expenses,
                self.delivery_to_main_carrier,
                self.export_formalities,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.FOB.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_unloading_to_point,
                self.delivery_to_unloading_port,
                self.export_formalities,
                self.loading_on_board,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.FAS.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_unloading_to_point,
                self.delivery_to_unloading_port,
                self.export_formalities,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.CFR.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_unloading_to_point,
                self.delivery_to_unloading_port,
                self.export_formalities,
                self.loading_on_board,
                self.transport_expenses_to_port,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.CIP.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_expenses,
                self.delivery_to_main_carrier,
                self.export_formalities,
                self.transport_expenses_to_port,
                self.products_insurance,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.CPT.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_expenses,
                self.delivery_to_main_carrier,
                self.export_formalities,
                self.transport_expenses_to_port,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.CIF.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_unloading_to_point,
                self.delivery_to_unloading_port,
                self.export_formalities,
                self.loading_on_board,
                self.transport_expenses_to_port,
                self.products_insurance,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.DDP.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_expenses,
                self.delivery_to_main_carrier,
                self.export_formalities,
                self.transport_expenses_to_port,
                self.unloading_on_seller,
                self.import_formalities,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.DAP.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.delivery_to_main_carrier,
                self.export_formalities,
                self.transport_expenses_to_port,
                self.unloading_on_seller,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)
        elif incoterm == Incoterm.DPU.value:
            nums = [
                self.product_price,
                self.packaging,
                self.product_check,
                self.loading_expenses,
                self.delivery_to_main_carrier,
                self.export_formalities,
                self.transport_expenses_to_port,
                self.unloading_on_terminal,
            ]
            nums = [str(num) for num in nums if num != 0]
            pre = f'{self.product_quantity} * ' if self.product_quantity > 1 else ""
            return pre + ' + '.join(nums)

    def get_formula(self, incoterm: str):
        formula_by_incoterm = {
            'EXW': 'КС = Цена производителя + Упаковка + Проверка товара',
            'FCA': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара основному перевозчику + Экспортные таможенные формальности и платежи',
            'FOB': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна',
            'FAS': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи',
            'CFR': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна + Транспортные расходы до порта назначения',
            'CIP': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на страхование груза',
            'CPT': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения',
            'CIF': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку-разгрузку при транспортировке до причала + Доставка товара до порта отгрузки + Экспортные таможенные формальности и платежи + Погрузка на борт судна + Транспортные расходы до порта назначения + Расходы на страхование груза',
            'DDP': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на разгрузку, которые по договору перевозки относятся к продавцу + Импортные таможенные формальности и платежи',
            'DAP': 'КС = Цена производителя + Упаковка + Проверка товара + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до места назначения + Расходы на разгрузку, которые по договору перевозки относятся к продавцу',
            'DPU': 'КС = Цена производителя + Упаковка + Проверка товара + Расходы на погрузку + Доставка товара перевозчику + Экспортные таможенные формальности и платежи + Транспортные расходы до терминала + Выгрузка товара на терминале',
        }

        return formula_by_incoterm[incoterm]

    def calculate_incoterm(self, incoterm: str):
        if incoterm == Incoterm.EXW.value:
            return self.product_price * self.product_quantity + self.packaging + self.product_check
        elif incoterm == Incoterm.FCA:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_expenses
                + self.delivery_to_main_carrier
                + self.export_formalities
            )
        elif incoterm == Incoterm.FOB.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_unloading_to_point
                + self.delivery_to_unloading_port
                + self.export_formalities
                + self.loading_on_board
            )
        elif incoterm == Incoterm.FAS.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_unloading_to_point
                + self.delivery_to_unloading_port
                + self.export_formalities
            )
        elif incoterm == Incoterm.CFR.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_unloading_to_point
                + self.delivery_to_unloading_port
                + self.export_formalities
                + self.loading_on_board
                + self.transport_expenses_to_port
            )
        elif incoterm == Incoterm.CIP.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_expenses
                + self.delivery_to_main_carrier
                + self.export_formalities
                + self.transport_expenses_to_port
                + self.products_insurance
            )
        elif incoterm == Incoterm.CPT.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_expenses
                + self.delivery_to_main_carrier
                + self.export_formalities
                + self.transport_expenses_to_port
            )
        elif incoterm == Incoterm.CIF.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_unloading_to_point
                + self.delivery_to_unloading_port
                + self.export_formalities
                + self.loading_on_board
                + self.transport_expenses_to_port
                + self.products_insurance
            )
        elif incoterm == Incoterm.DDP.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_expenses
                + self.delivery_to_main_carrier
                + self.export_formalities
                + self.transport_expenses_to_port
                + self.unloading_on_seller
                + self.import_formalities
            )
        elif incoterm == Incoterm.DAP.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.delivery_to_main_carrier
                + self.export_formalities
                + self.transport_expenses_to_port
                + self.unloading_on_seller
            )
        elif incoterm == Incoterm.DPU.value:
            return (
                self.product_price * self.product_quantity
                + self.packaging
                + self.product_check
                + self.loading_expenses
                + self.delivery_to_main_carrier
                + self.export_formalities
                + self.transport_expenses_to_port
                + self.unloading_on_terminal
            )


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


class PR1ControlInfo(BaseModel):
    steps: list[Step]
    control_test_questions: list[TestQuestionPR1]


class UserCredentials(BaseModel):
    username: str
    password: str


class UserUpdate(UserBase):
    id: int
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    username: Optional[str] = None


class ResponseMessage(BaseModel):
    message: str


class UserToApprove(BaseModel):
    id: int
    first_name: str
    last_name: str
    surname: Optional[str] = None
    group_name: str


class UserChangePassword(BaseModel):
    password: str


class CheckpointData(BaseModel):
    computer_id: int
    event_id: str
    step_code: Union[PR1ClassStep, PR1ControlStep]
    text: Optional[str]
    answer_ids: Optional[list[int]] = []
    chosen_index: Optional[int]
    chosen_incoterm: Optional[Incoterm]
    chosen_letter: Optional[str] = None
    formula: Optional[str]


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
    common_bets_ids_chosen_by_seller: Optional[dict[str, list[int]]] = {}
    describe_option: Optional[str] = None
    options_comparison: Optional[dict[Incoterm, IncotermInfo]]
    chosen_option: Optional[ChosenOption]
    tests: Optional[list[list[TestQuestionPR1]]]
    test_results: Optional[list[list[EventStepResult]]] = [[], [], []]
    results: Optional[list[PR1ClassResults]] = []


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


class CheckpointResponse(BaseModel):
    status: Optional[str] = None
    next_step: Optional[Union[Step, str]] = None
    fails: Optional[int] = 0
    missed_ids: Optional[list[int]] = []
    not_needed_ids: Optional[list[int]] = []
