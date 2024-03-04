import random
import logging
from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from constants.practice_one_info import practice_one_info
from db.state import state
from schemas import (
    StartEventDto,
    CheckpointData,
    StartEventResponse,
    EventInfo,
    EventType,
    EventMode,
    PR1ClassEvent,
    CheckpointResponse, ConnectedComputer, Step, EventStatus, CurrentStepResponse, IncotermInfoSummarize, Incoterm,
)
from db.mongo import get_db, CollectionNames
from services.create_event import create_event
from services.event import EventService
from services.oauth2 import extract_users_ids_rest
from services.practice_one_class import PracticeOneClass
from services.utils import normalize_mongo
from services.ws import broadcast_connected_computers

router = APIRouter(tags=['Events'], prefix='/events')

event_service = EventService(db=get_db())

logger = logging.getLogger(__name__)


@router.post('/start', response_model=StartEventResponse)
async def start_event(start_event_dto: StartEventDto, users_ids: list[str] = Depends(extract_users_ids_rest)):
    if not users_ids:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Юзеры не найдены")

    event = create_event(event_dto=start_event_dto, users_ids=users_ids)

    connected_computer = ConnectedComputer(
        id=start_event_dto.computer_id,
        users_ids=event.users_ids,
        event_type=event.event_type,
        event_mode=event.event_mode,
        step=event.current_step,
    )
    state.upsert_connected_computer(connected_computer)

    print(f"EVENT_ID is {event.id}")

    return StartEventResponse(event_id=event.id)


@router.get('/active')
async def find_active_or_not_finished_events(
    users_ids: list[str] = Depends(extract_users_ids_rest), db: Database = Depends(get_db)
):
    events_db = list(
        db[CollectionNames.EVENTS.value].find(
            {'is_finished': False, 'users_ids': {'$size': len(users_ids), '$all': users_ids}}
        )
    )

    # TODO
    # if len(events_db) > 1:
    #     raise Exception("Не может быть больше 1 долга")

    return normalize_mongo(events_db, EventInfo)


@router.get('/current-step', status_code=status.HTTP_200_OK, response_model=CurrentStepResponse)
async def get_current_step(
        event_id: str,
        users_ids: list[str] = Depends(extract_users_ids_rest),
        db: Database = Depends(get_db)
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вариант не найден')

    pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)

    current_step_response = CurrentStepResponse(
        current_step=pr1_class_event.current_step,
    )

    if pr1_class_event.is_finished and "TEST" not in pr1_class_event.current_step.code:
        current_step_response.is_finished = True
        return current_step_response

    if pr1_class_event.current_step.code == "OPTIONS_COMPARISON":
        options_comparison = PracticeOneClass(users_ids).get_options_comparison(pr1_class_event)
        pr1_class_event.options_comparison = options_comparison
        db[CollectionNames.EVENTS.value].update_one({"_id": ObjectId(pr1_class_event.id)}, {
            "$set": {
                "options_comparison": {key: value.dict() for key, value in options_comparison.items()}
            }
        })
        current_step_response.options_comparison = options_comparison
    elif pr1_class_event.current_step.code == "CONDITIONS_SELECTION":
        current_step_response.delivery_options = {
            key: IncotermInfoSummarize(
                agreement_price_seller=option.agreement_price_seller,
                delivery_price_buyer=option.delivery_price_buyer,
                total=option.total
            ).dict() for key, option in pr1_class_event.options_comparison.items()
        }
    elif 'BUYER' in pr1_class_event.current_step.code or 'SELLER' in pr1_class_event.current_step.code:
        random.shuffle(pr1_class_event.bets)
        current_step_response.bets = pr1_class_event.bets
    elif pr1_class_event.current_step.code == 'SELECT_LOGIST':
        current_step_response.logists = pr1_class_event.logists
    elif 'TEST' in pr1_class_event.current_step.code:
        if pr1_class_event.test_index > 2:
            current_step_response.is_finished = True
        index = int(pr1_class_event.current_step.code[5:]) - 1
        current_step_response.test_question = pr1_class_event.tests[pr1_class_event.test_index][index]

    return current_step_response


@router.post('/checkpoint', response_model=CheckpointResponse)
async def create_checkpoint(
    checkpoint_dto: CheckpointData,
    # users_ids: list[str] = Depends(extract_users_ids_rest),
    db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(checkpoint_dto.event_id)})

    if not event_db:
        raise Exception('Вариант не найден')

    if event_db['is_finished']:
        return Step(id=-1, code="FINISHED", name=f"Работа завершена", role="ALL")

    checkpoint_response = None

    if event_db['event_type'] == EventType.PR1.value:
        if event_db['event_mode'] == EventMode.CLASS.value:
            event = normalize_mongo(event_db, PR1ClassEvent)
            checkpoint_response = PracticeOneClass(computer_id=checkpoint_dto.computer_id, users_ids=event.users_ids).checkpoint(
                event, checkpoint_dto
            )

    state.update_connected_computer_checkpoint(checkpoint_dto.computer_id, checkpoint_response.next_step)
    await broadcast_connected_computers()

    return checkpoint_response


@router.get('/results')
async def get_results(
        event_id: str,
        db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise Exception('Вариант не найден')

    event = normalize_mongo(event_db, EventInfo)

    if event.results:
        return event.results

    if event_db['event_type'] == EventType.PR1.value:
        if event_db['event_mode'] == EventMode.CLASS.value:
            event = normalize_mongo(event_db, PR1ClassEvent)
            return PracticeOneClass(users_ids=event.users_ids).get_results(event)


@router.get('/pr1-class-right-checkpoints')
async def get_right_checkpoints(event_id: str):
    db: Database = get_db()
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    event = normalize_mongo(event_db, PR1ClassEvent)

    checkpoints = []
    for step in practice_one_info.steps:
        checkpoint = {'step_code': step.code}
        if 'SELLER' in step.code or 'BUYER' in step.code:
            right_bets_ids = []
            for bet in practice_one_info.bets:
                incoterm = step.code[:3]
                if 'SELLER' in step.code:
                    if incoterm in bet.incoterms.seller:
                        right_bets_ids.append(bet.id)
                if 'BUYER' in step.code:
                    if incoterm in bet.incoterms.buyer or incoterm in bet.incoterms.common:
                        right_bets_ids.append(bet.id)
            checkpoint['answer_ids'] = right_bets_ids
        elif step.code == 'SELECT_LOGIST':
            checkpoint['chosen_index'] = 2
        elif step.code == "OPTIONS_COMPARISON":
            pass
        elif step.code == "CONDITIONS_SELECTION":
            checkpoint['chosen_incoterm'] = 'EXW'
        elif step.code == 'DESCRIBE_OPTION':
            checkpoint['text'] = 'Described.'
        checkpoints.append(checkpoint)

    for i in range(20):
        checkpoint = {"step_code": f"TEST_{i + 1}"}
        right_options_ids = [option.id for option in event.tests[0][i].options if option.is_correct]
        checkpoint['answer_ids'] = right_options_ids
        checkpoints.append(checkpoint)

    return checkpoints


@router.get('/pr1-class-hints', response_model=str)
async def get_p1_class_hints(incoterm: Incoterm):
    return practice_one_info.hints[incoterm]


@router.post('/retake-test')
async def retake_test(
        event_id: str,
        db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({"_id": ObjectId(event_id)})
    if not event_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event не найден")

    event = normalize_mongo(event_db, EventInfo)

    if event.event_mode != EventMode.CLASS or event.event_type != EventType.PR1:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    if event.event_mode == EventMode.CLASS and event.event_type == EventType.PR1:
        if not event.is_finished:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сначала закончите работу!")

        pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)

        if pr1_class_event.test_index >= 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Вы использовали все попытки")

        if len(pr1_class_event.test_results[pr1_class_event.test_index]) < 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сначала завершите прошлый тест")

        first_test_step = Step(
            id=len(practice_one_info.steps),
            code=f"TEST_1",
            name="Тестовый вопрос №1",
            role="ALL",
        )

        db[CollectionNames.EVENTS.value].update_one({"_id": ObjectId(event_id)}, {
            "$inc": {
                "test_index"
            },
            "current_step": first_test_step.dict()
        })
