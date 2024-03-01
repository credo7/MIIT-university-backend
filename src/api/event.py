import random
import logging
from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database

from db.state import state
from schemas import (
    StartEventDto,
    CheckpointData,
    StartEventResponse,
    EventInfo,
    EventType,
    EventMode,
    PR1ClassEvent,
    CheckpointResponse, ConnectedComputer, Step, EventStatus, CurrentStepResponse, IncotermInfoSummarize,
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


@router.get('/current-step/', status_code=status.HTTP_200_OK, response_model=CurrentStepResponse)
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

    if pr1_class_event.is_finished:
        current_step_response.is_finished = True

    print(f"\n\npr1_class_event.current_step.code={pr1_class_event.current_step.code}\n\n")

    if pr1_class_event.current_step.code == "OPTIONS_COMPARISON":
        options_comparison = PracticeOneClass(users_ids).get_options_comparison(pr1_class_event)
        print(f"\n\noptions_comparison___={options_comparison}\n\n")
        pr1_class_event.options_comparison = options_comparison
        print("9999")
        print(f"options_comparison={options_comparison}")
        db[CollectionNames.EVENTS.value].update_one({"_id": ObjectId(pr1_class_event.id)}, {
            "$set": {
                "options_comparison": {key: value.dict() for key, value in options_comparison.items()}
            }
        })
        current_step_response.options_comparison = options_comparison
    elif pr1_class_event.current_step.code == "CONDITIONS_SELECTION":
        current_step_response.delivery_options = {key: IncotermInfoSummarize(**value).dict() for key, value in pr1_class_event.options_comparison}
    elif 'BUYER' in pr1_class_event.current_step.code or 'SELLER' in pr1_class_event.current_step.code:
        random.shuffle(pr1_class_event.bets)
        current_step_response.bets = pr1_class_event.bets
    elif pr1_class_event.current_step.code == 'SELECT_LOGIST':
        current_step_response.logists = pr1_class_event.logists
    elif 'TEST' in pr1_class_event.current_step.code:
        index = int(pr1_class_event.current_step.code[5:]) - 1
        current_step_response.test_question = pr1_class_event.test[index]

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
        return 'FINISHED'

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


#     event = event_service.get_current_event_by_user_id(current_user)
#     if event.is_finished:
#         return {'results': event.results}
#
#     is_last_checkpoint = event_service.is_last_checkpoint(event)
#
#     event_service.create_checkpoint(event, checkpoint_dto, is_last_checkpoint)
#
#     results = None
#     if is_last_checkpoint:
#         results = event_service.finish_event(event)
#
#     next_step = None
#     if not results:
#         # Косяк. Делаем так, потому что внутри предыдущих функций используем другой инстанс евента
#         event.step_index += 1
#         next_step = event_service.get_current_step(event)
#
#     await broadcast_connected_computers()
#
#     return {'next_step': next_step.dict()} if not results else {'results': results}
#
#
# @router.get('/current-step/{computer_id}')
# async def get_current_step(computer_id: int):
#     event = event_service.get_current_event_by_computer_id(computer_id)
#
#     if event.is_finished:
#         return event.results
#
#     current_step = event_service.get_current_step(event)
#
#     logger.info(f'current_step = {current_step}')
#
#     return current_step
