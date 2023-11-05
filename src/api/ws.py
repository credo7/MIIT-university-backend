import logging
from typing import Dict, Any, List, Union

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.sql.expression import func

import db.shared_state
import models
from schemas import WSMessage, WSCommandTypes, ConnectedComputer, EventType
from services.connection_manager import ConnectionManager
from services.data_service import DataService
from db.postgres import session as session_db
from services.event import EventService
from db.shared_state import shared_state

router = APIRouter(tags=['ws'], prefix='')

connected_computers: Dict[int, ConnectedComputer] = {}

manager = ConnectionManager()

lesson = None

data_service = DataService(session_db)

event_service = EventService(session_db)


async def broadcast_connected_computers():
    dict_connected_computers = [{key: v.dict()} for key, v in connected_computers.items()]
    await manager.broadcast(dict_connected_computers)


async def disconnect(websocket: WebSocket, computer_id: int):
    if computer_id in connected_computers:
        connected_computers[computer_id].is_connected = False
    manager.disconnect(websocket)
    await broadcast_connected_computers()


async def raise_if_users_connected(users_ids: List[int]):
    """Проверяем студентов на уникальность, может он уже подключен к другому компьютеру"""
    for computer_id, connected_computer in connected_computers.items():
        for user_id in users_ids:
            if user_id in connected_computer.users_ids:
                raise Exception(f"Студент с user_id {user_id} уже подключен за компьтер с номером {computer_id}")


async def actualize_computer_state(computer_id: int, payload: Any):
    connected_computer = ConnectedComputer(**payload, is_connected=True, is_started=False)
    await raise_if_users_connected(connected_computer.users_ids)
    connected_computers[computer_id] = connected_computer
    await broadcast_connected_computers()


class EventStartValidation:
    def __init__(self):
        ...

    async def validate(self):
        await self.computers_exist()
        await self.identical_type_mode()

    @staticmethod
    async def computers_exist():
        if len(connected_computers) < 1:
            raise Exception("Нет подключенных компьютеров")

    @staticmethod
    async def identical_type_mode():
        """На одном уроке ученики могут выбрать только одинаковый тип работы и режим"""
        types = set()
        mode = set()

        for connected_computer in connected_computers.values():
            types.add(connected_computer.event_type)
            mode.add(connected_computer.event_mode)

        if len(types) > 1:
            raise Exception("Выбраны разные типы работ")

        if len(mode) > 1:
            raise Exception("Выбраны разные режимы работ")


async def remove_disconnected_computers():
    """Удаляем юзеров из connected_computers возможно они зашли случайно, а после перезашли с другого компьютера"""
    for computer_id, connected_computer in connected_computers.items():
        if connected_computer.is_connected is False:
            del connected_computers[computer_id]


async def generate_events():
    variant_models = {
        EventType.PR1: models.PracticeOneVariant,
        EventType.PR2: models.PracticeTwoVariant,
        EventType.CONTROL: ...
    }

    events = []

    for computer_id, connected_computer in connected_computers.items():
        model = variant_models[connected_computer.event_type]
        random_variant = session_db.query(model).order_by(func.random()).first()

        new_event = models.Event(
            lesson_id=lesson.id,
            computer_id=computer_id,
            type=connected_computer.event_type.value,
            mode=connected_computer.event_mode.value,
            variant_one_id=random_variant.id if model == models.PracticeOneVariant else None,
            variant_two_id=random_variant.id if model == models.PracticeTwoVariant else None,
            user_1_id=connected_computer.users_ids[0],
            user_2_id=connected_computer.users_ids[0] if len(connected_computer.users_ids) > 1 else None,
        )

        events.append(new_event)

    return events


async def start_events(*args):
    global lesson
    if lesson is not None:
        # TODO: FINISH ALL OTHER EVENTS
        ...
    await remove_disconnected_computers()
    await EventStartValidation().validate()

    lesson = await data_service.create_lesson()
    shared_state.lesson_id = lesson.id
    events = await generate_events()
    await data_service.insert_events(events)
    ws_msg = {"type": "STATUS", "payload": "START"}
    await manager.broadcast(ws_msg)


ws_handlers = {
    WSCommandTypes.SELECT_TYPE: actualize_computer_state,
    WSCommandTypes.START: start_events
}


@router.websocket("/ws/{computer_id}")
async def websocket_endpoint(websocket: WebSocket, computer_id: int):
    print(f"websocket.headers = {websocket.headers}")
    await manager.connect(websocket)
    # Если компьютер уже был подключен, то активируем статус коннектед и броадкастим
    if computer_id in connected_computers:
        connected_computers[computer_id].is_connected = True
        await broadcast_connected_computers()
    # try:
    while True:
        data = await websocket.receive_json()
        message = WSMessage(**data)
        print(f"computer_id={computer_id}\ntype={message.type}\npayload={message.payload}")
        await ws_handlers[message.type](computer_id, message.payload)
    # except WebSocketDisconnect:
    #     await disconnect(websocket, computer_id)
    # except Exception as err:
    #     ws_error = {"type": "ERROR", "payload": str(err)}
    #     await manager.broadcast(ws_error)
