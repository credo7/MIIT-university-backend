import asyncio
import logging
import time
from copy import deepcopy
from typing import Union

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pymongo.database import Database

import schemas
from constants.practice_one_info import practice_one_info
from db.mongo import (
    CollectionNames,
    get_db,
)
from db.state import WebsocketServiceState
from schemas import (
    AllowedModes,
    CheckpointData,
    CheckpointResponse,
    ConnectedComputer,
    CurrentStepResponse,
    EventInfo,
    EventMode,
    EventType,
    Incoterm,
    MiniUser,
    PR1ClassEvent,
    PR1ControlEvent,
    PR2ClassEvent,
    StartEventDto,
    StartEventResponse,
    Step, ConnectedComputerUpdate,
)
from services import oauth2
from services.create_event import create_event
from services.oauth2 import extract_users_ids_rest
from services.practice_one_class import PracticeOneClass
from services.practice_one_control import PracticeOneControl
from services.practice_two_class import PracticeTwoClass
from services.utils import normalize_mongo

router = APIRouter(tags=['Events'], prefix='/events')

logger = logging.getLogger(__name__)


@router.post('/start', response_model=StartEventResponse)
async def start_event(start_event_dto: StartEventDto, users_ids: list[str] = Depends(extract_users_ids_rest)):
    if not users_ids:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Юзеры не найдены')

    if start_event_dto.type == EventType.PR1 and start_event_dto.mode == EventMode.CLASS:
        event = PracticeOneClass(computer_id=start_event_dto.computer_id, users_ids=users_ids).create(start_event_dto)
    elif start_event_dto.type == EventType.PR1 and start_event_dto.mode == EventMode.CONTROL:
        event = PracticeOneControl(computer_id=start_event_dto.computer_id, users_ids=users_ids).create(start_event_dto)
    elif start_event_dto.type == EventType.PR2 and start_event_dto.mode == EventMode.CLASS:
        event = PracticeTwoClass(computer_id=start_event_dto.computer_id, users_ids=users_ids).create(start_event_dto)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Неизвестный режим. type={start_event_dto.type}. mode={start_event_dto.mode}',
        )

    if WebsocketServiceState.is_computer_exists_and_same_users(start_event_dto.computer_id, event.users_ids):
        computer_update = ConnectedComputerUpdate(
            id=start_event_dto.computer_id,
            event_id=event.id,
            event_type=event.event_type,
            event_mode=event.event_mode,
        )
        await WebsocketServiceState.update_connected_computer(computer_update)
    else:
        connected_computer = ConnectedComputer(
            id=start_event_dto.computer_id,
            users_ids=event.users_ids,
            event_type=event.event_type,
            event_mode=event.event_mode,
            step_code=event.current_step.code if isinstance(event.current_step, Step) else event.current_step,
            event_id=event.id,
            last_action=time.time(),
        )
        await WebsocketServiceState.create_connected_computer(connected_computer)

    return StartEventResponse(event_id=event.id)


@router.get('/allowed')
async def get_allowed_modes(
    users_ids: list[str] = Depends(extract_users_ids_rest), db: Database = Depends(get_db)
) -> list[AllowedModes]:
    allowed_modes = [AllowedModes.PR1_CLASS, AllowedModes.PR1_CONTROL, AllowedModes.PR2_CLASS]

    for user_id in users_ids:
        at_least_one_finished_pr1_class = db[CollectionNames.EVENTS.value].find_one(
            {'users_ids': {'$in': [user_id]}, 'event_type': 'PR1', 'event_mode': 'CLASS', 'is_finished': True}
        )
        if at_least_one_finished_pr1_class is None:
            allowed_modes.remove(AllowedModes.PR1_CONTROL)
            allowed_modes.remove(AllowedModes.PR2_CLASS)

    return allowed_modes


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
    event_id: str, users_ids: list[str] = Depends(extract_users_ids_rest), db: Database = Depends(get_db)
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вариант не найден')

    event = normalize_mongo(event_db, EventInfo)

    if event.event_type == EventType.PR1 and event.event_mode == EventMode.CLASS:
        pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)
        return PracticeOneClass(computer_id=pr1_class_event.computer_id, users_ids=users_ids).get_current_step(
            pr1_class_event
        )
    elif event.event_type == EventType.PR1 and event.event_mode == EventMode.CONTROL:
        pr1_control_event = normalize_mongo(event_db, PR1ControlEvent)
        return PracticeOneControl(computer_id=pr1_control_event.computer_id, users_ids=users_ids).get_current_step(
            pr1_control_event
        )
    elif event.event_type == EventType.PR2 and event.event_mode == EventMode.CLASS:
        pr2_class_event = normalize_mongo(event_db, PR2ClassEvent)
        return PracticeTwoClass(computer_id=pr2_class_event.computer_id, users_ids=users_ids).get_current_step(
            pr2_class_event
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Неизвестный режим. type={event.event_type}. mode={event.event_mode}',
        )


@router.post('/checkpoint', response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
async def create_checkpoint(
    checkpoint_dto: CheckpointData,
    # users_ids: list[str] = Depends(extract_users_ids_rest),
    db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(checkpoint_dto.event_id)})

    if not event_db:
        raise Exception('Вариант не найден')

    # if event_db['is_finished']:
    #     return Step(id=-1, code="FINISHED", name=f"Работа завершена", role="ALL")

    event_info = normalize_mongo(event_db, EventInfo)

    checkpoint_response = None

    if event_info.event_type == EventType.PR1 and event_info.event_mode == EventMode.CLASS:
        event = normalize_mongo(event_db, PR1ClassEvent)
        checkpoint_response = PracticeOneClass(
            computer_id=checkpoint_dto.computer_id, users_ids=event.users_ids
        ).checkpoint(event, checkpoint_dto)

    if event_info.event_type == EventType.PR1 and event_info.event_mode == EventMode.CONTROL:
        event = normalize_mongo(event_db, PR1ControlEvent)
        checkpoint_response = PracticeOneControl(
            computer_id=checkpoint_dto.computer_id, users_ids=event.users_ids
        ).checkpoint(event, checkpoint_dto)

    if event_info.event_type == EventType.PR2 and event_info.event_mode == EventMode.CLASS:
        event = normalize_mongo(event_db, PR2ClassEvent)
        checkpoint_response = PracticeTwoClass(
            computer_id=checkpoint_dto.computer_id, users_ids=event.users_ids
        ).checkpoint(event, checkpoint_dto)

    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(checkpoint_dto.event_id)})
    if not event_db:
        raise Exception('Вариант не найден')
    event_info = normalize_mongo(event_db, EventInfo)

    if WebsocketServiceState.is_computer_exists_and_same_users(event_info.computer_id, event_info.users_ids):
        computer_update = ConnectedComputerUpdate(
            id=event_info.computer_id,
            step_code=event_info.current_step.code if isinstance(event_info.current_step, Step) else event_info.current_step,
            event_type=event_info.event_type,
            event_mode=event_info.event_mode,
            event_id=event_info.id,
        )
        await WebsocketServiceState.update_connected_computer(computer_update)
    else:
        connected_computer = ConnectedComputer(
            id=event_info.computer_id,
            users_ids=event_info.users_ids,
            event_type=event_info.event_type,
            event_mode=event_info.event_mode,
            step_code=event_info.current_step.code if isinstance(event_info.current_step, Step) else event_info.current_step,
            event_id=event_info.id,
            last_action=time.time()
        )
        await WebsocketServiceState.create_connected_computer(connected_computer)

    if event_info.current_step == "FINISHED" or (isinstance(event_info.current_step, Step) and event_info.current_step.code == "FINISHED"):
        computer_update = ConnectedComputerUpdate(
            id=event_info.computer_id,
            help_requested=False
        )
        await WebsocketServiceState.update_connected_computer(computer_update)

    return checkpoint_response


@router.get('/results', status_code=status.HTTP_200_OK)
async def get_results(
    event_id: str, db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Вариант не найден')

    event = normalize_mongo(event_db, EventInfo)

    if not event.is_finished:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вариант не закончен')

    if not event.results:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Как так вышло?')

    return event.results


@router.get('/pr1-class-right-checkpoints', status_code=status.HTTP_200_OK)
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
            checkpoint['chosen_letter'] = 'Б'
        elif step.code == 'OPTIONS_COMPARISON':
            pass
        elif step.code == 'CONDITIONS_SELECTION':
            checkpoint['chosen_incoterm'] = 'EXW'
        elif step.code == 'DESCRIBE_OPTION':
            checkpoint['text'] = 'Described.'
        checkpoints.append(checkpoint)

    for i in range(20):
        checkpoint = {'step_code': f'TEST_{i + 1}'}
        right_options_ids = [option.id for option in event.tests[0][i].options if option.is_correct]
        checkpoint['answer_ids'] = right_options_ids
        checkpoints.append(checkpoint)

    return checkpoints


@router.get('/pr1-class-hints', response_model=str, status_code=status.HTTP_200_OK)
async def get_p1_class_hints(incoterm: Incoterm):
    return practice_one_info.hints[incoterm]


@router.post('/retake-test', status_code=status.HTTP_200_OK)
async def retake_test(
    event_id: str, db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})
    if not event_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Event не найден')

    event = normalize_mongo(event_db, EventInfo)
    if event.event_mode != EventMode.CLASS or event.event_type != EventType.PR1:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)

    if event.event_mode == EventMode.CLASS and event.event_type == EventType.PR1:
        if not event.is_finished:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Сначала закончите работу!')

        pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)

        if pr1_class_event.test_index >= 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вы использовали все попытки')

        if len(pr1_class_event.test_results[pr1_class_event.test_index]) < 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Сначала завершите прошлый тест')

        first_test_step = Step(id=len(practice_one_info.steps), code=f'TEST_1', name='Тестовый вопрос №1', role='ALL',)

        db[CollectionNames.EVENTS.value].update_one(
            {'_id': ObjectId(event_id)},
            {
                '$inc': {'test_index': 1},
                '$set': {'current_step': first_test_step.dict(), 'is_finished': False, 'result': None},
            },
        )

        for user_id in event.users_ids:
            db[CollectionNames.USERS.value].update_one({'_id': ObjectId(user_id)}, {'$pop': {'history': 1}})

        for comp_id, comp in WebsocketServiceState.connected_computers.items():
            if comp.event_id == event_id:
                computer_update = ConnectedComputerUpdate(
                    id=comp_id,
                    step_code=first_test_step.code
                )
                await WebsocketServiceState.update_connected_computer(computer_update)
                break

@router.post('/continue-work', status_code=status.HTTP_200_OK)
async def continue_work(
    event_id: str,
    db: Database = Depends(get_db),
    # _users_ids: list[str] = Depends(extract_users_ids_rest),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Вариант не найден')

    event = normalize_mongo(event_db, EventInfo)

    if event.event_mode != EventMode.CLASS.value or event.event_type != EventType.PR1.value:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail='Пока работает только для классной работы PR1'
        )

    if event.is_finished:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Работа уже завершена')

    if event.event_type == EventType.PR1.value:
        if event.event_mode == EventMode.CLASS.value:
            pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)
            PracticeOneClass(users_ids=event.users_ids).continue_work(pr1_class_event)


@router.get('/computers-states', response_model=list[schemas.ConnectedComputerFrontResponse])
async def get_all_computers_states(db: Database = Depends(get_db)):

    connected_computers = deepcopy(WebsocketServiceState.connected_computers)

    for conn_computer_id, conn_computer in connected_computers.items():
        if not conn_computer.is_connected and conn_computer.is_expired():
            await WebsocketServiceState.remove_connected_computer(conn_computer_id)

    connected_computers_front = []
    for connected_computer in WebsocketServiceState.connected_computers.values():
        mini_users = []
        for user_id in connected_computer.users_ids:
            user_db = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user_id)})
            user = normalize_mongo(user_db, schemas.MiniUser)
            mini_users.append(user)

        percentage = 0
        if connected_computer.event_id is None or connected_computer.step_code is None:
            percentage = 0
        elif connected_computer.event_type == EventType.PR1 and connected_computer.event_mode == EventMode.CLASS:
            percentage = get_pr1_class_percentage(connected_computer.step_code)
        elif connected_computer.event_type == EventType.PR1 and connected_computer.event_mode == EventMode.CONTROL:
            percentage = get_pr1_control_percentage(connected_computer.step_code)
        elif connected_computer.event_type == EventType.PR2 and connected_computer.event_mode == EventMode.CLASS:
            percentage = get_pr2_class_percentage(connected_computer.step_code)

        connected_computers_front.append(
            schemas.ConnectedComputerFrontResponse(**connected_computer.dict(), users=mini_users, percentage=percentage)
        )

    return connected_computers_front


@router.get('/{event_id}')
async def get_event(event_id: str, db: Database = Depends(get_db)):
    print(f'event_id={event_id}')
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Вариант не найден')

    event = normalize_mongo(event_db, EventInfo)

    if event.event_type == EventType.PR1 and event.event_mode == EventMode.CLASS:
        return normalize_mongo(event_db, PR1ClassEvent)

    if event.event_type == EventType.PR1 and event.event_mode == EventMode.CONTROL:
        return normalize_mongo(event_db, PR1ControlEvent)

    if event.event_type == EventType.PR2 and event.event_mode == EventMode.CLASS:
        return normalize_mongo(event_db, PR2ClassEvent)

    if event.event_type != EventType.PR1:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f'Мод либо тип не найдены. event_type={event.event_type}. event_mode={event.event_mode}',
        )


def get_pr1_class_percentage(step_code: Union[str, int]):
    pr1_class_percentages = {
        'SELECT_LOGIST': 2,
        'EXW_BUYER': 6,
        'EXW_SELLER': 8,
        'FCA_BUYER': 10,
        'FCA_SELLER': 12,
        'CPT_BUYER': 14,
        'CPT_SELLER': 16,
        'CIP_BUYER': 18,
        'CIP_SELLER': 20,
        'DAP_BUYER': 22,
        'DAP_SELLER': 24,
        'DPU_BUYER': 26,
        'DPU_SELLER': 28,
        'DDP_BUYER': 30,
        'DDP_SELLER': 32,
        'FAS_BUYER': 34,
        'FAS_SELLER': 36,
        'FOB_BUYER': 38,
        'FOB_SELLER': 40,
        'CFR_BUYER': 42,
        'CFR_SELLER': 44,
        'CIF_BUYER': 46,
        'CIF_SELLER': 48,
        'OPTIONS_COMPARISON': 50,
        'CONDITIONS_SELECTION': 54,
        'DESCRIBE_OPTION': 58,
        'TEST_1': 60,
        'TEST_2': 62,
        'TEST_3': 64,
        'TEST_4': 66,
        'TEST_5': 68,
        'TEST_6': 70,
        'TEST_7': 72,
        'TEST_8': 74,
        'TEST_9': 76,
        'TEST_10': 78,
        'TEST_11': 80,
        'TEST_12': 82,
        'TEST_13': 84,
        'TEST_14': 86,
        'TEST_15': 88,
        'TEST_16': 90,
        'TEST_17': 92,
        'TEST_18': 94,
        'TEST_19': 96,
        'TEST_20': 98,
        'FINISHED': 100,
    }
    if step_code not in pr1_class_percentages:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Такой step_code не найден')
    return pr1_class_percentages[step_code]


def get_pr1_control_percentage(step_code: Union[str, int]):
    pr1_control_percentage = {
        'PR1_CONTROL_1': 5,
        'PR1_CONTROL_2': 20,
        'PR1_CONTROL_3': 40,
        'TEST_1': 60,
        'TEST_2': 62,
        'TEST_3': 64,
        'TEST_4': 66,
        'TEST_5': 68,
        'TEST_6': 70,
        'TEST_7': 72,
        'TEST_8': 74,
        'TEST_9': 76,
        'TEST_10': 78,
        'TEST_11': 80,
        'TEST_12': 82,
        'TEST_13': 84,
        'TEST_14': 86,
        'TEST_15': 88,
        'TEST_16': 90,
        'TEST_17': 92,
        'TEST_18': 94,
        'TEST_19': 96,
        'TEST_20': 98,
        'FINISHED': 100,
    }

    if step_code not in pr1_control_percentage:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Такой степ не найден')
    return pr1_control_percentage[step_code]


def get_pr2_class_percentage(step_code: Union[str, int]):
    pr2_class_percentages = {
        'SCREEN_1_INSTRUCTION_WITH_LEGEND': 1,
        'SCREEN_2_TASK_DESCRIPTION': 4,
        'SCREEN_3_SOURCE_DATA_FULL_ROUTES': 8,
        'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME': 10,
        'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME': 12,
        'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER': 14,
        'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION': 16,
        'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY': 18,
        'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME': 20,
        'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME': 22,
        'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER': 24,
        'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION': 26,
        'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY': 28,
        'SCREEN_5_DESCRIBE_CONTAINER_SELECTION': 30,
        'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_1': 32,
        'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_2': 34,
        'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_3': 36,
        'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_4': 38,
        'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_5': 40,
        'SCREEN_7_SOURCE_DATA_CHOOSE_DESTINATIONS': 42,
        'SCREEN_7_SOURCE_DATA_CHOOSE_PORTS': 45,
        'SCREEN_7_SOURCE_DATA_CHOOSE_BORDER': 48,
        'SCREEN_8_MAP_ROUTE_1': 51,
        'SCREEN_8_MAP_ROUTE_2': 54,
        'SCREEN_8_MAP_ROUTE_3': 57,
        'SCREEN_8_MAP_ROUTE_4': 60,
        'SCREEN_8_MAP_ROUTE_5': 63,
        'SCREEN_8_MAP_ROUTE_6': 66,
        'SCREEN_8_MAP_ROUTE_7': 69,
        'SCREEN_8_MAP_ROUTE_8': 72,
        'SCREEN_9_FORMED_ROUTES_TABLE': 75,
        'SCREEN_10_RISKS_1': 76,
        'SCREEN_10_RISKS_2': 78,
        'SCREEN_10_RISKS_3': 80,
        'SCREEN_10_RISKS_4': 82,
        'SCREEN_10_RISKS_TOTAL': 84,
        'SCREEN_10_FULL_ROUTES_WITH_PLS': 85,
        'SCREEN_11_OPTIMAL_RESULTS_3PL1': 88,
        'SCREEN_11_OPTIMAL_RESULTS_3PL2': 91,
        'SCREEN_11_OPTIMAL_RESULTS_3PL3': 94,
        'SCREEN_11_OPTIMAL_RESULTS_COMBO': 97,
        'SCREEN_13_CHOOSE_LOGIST': 99,
        'FINISHED': 100,
    }

    if step_code not in pr2_class_percentages:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Такой степ не найден')
    return pr2_class_percentages[step_code]
