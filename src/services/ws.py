import copy
import logging
from typing import List, Optional, Dict

from db.state import state
from fastapi import WebSocket

from schemas import UserOut, ConnectedComputerEdit, EventStatus, ConnectedComputer
from services.utils import raise_if_users_already_connected

logger = logging.getLogger(__name__)


async def broadcast_connected_computers():
    connected_computers = await state.get_connected_computers()
    dict_connected_computers = [{key: v.dict()} for key, v in connected_computers.items()]
    await state.manager.broadcast(dict_connected_computers)
    logger.info(f'connected_computers={connected_computers}')


async def disconnect(
    ws: WebSocket, computer_id: int, is_teacher, users_ids: List[UserOut], error: Optional[Dict] = None
):
    state.manager.disconnect(ws)

    logger.info(f'computer_id:{computer_id} was disconnected. is_teacher={is_teacher}.' f' users_ids={users_ids}')

    connected_computers = await state.get_connected_computers()

    if not is_teacher and computer_id in connected_computers:
        connected_computer_edit = ConnectedComputerEdit(id=computer_id, is_connected=False)
        await state.edit_connected_computer(connected_computer_edit)
        await broadcast_connected_computers()

    if error is not None:
        await state.manager.broadcast(error)


async def raise_if_users_connected(users_ids: List[str]):
    """Проверяем студентов на уникальность, может он уже подключен к другому компьютеру"""
    connected_computers = await state.get_connected_computers()
    for computer_id, connected_computer in connected_computers.items():
        for user_id in users_ids:
            if connected_computer.users_ids and user_id in connected_computer.users_ids:
                raise Exception(f'Студент с user_id {user_id} уже подключен за компьтер с номером {computer_id}')


async def connect_with_broadcast(websocket: WebSocket, users: List[UserOut], computer_id: int, is_teacher: bool):
    await state.manager.connect(websocket)

    if is_teacher:
        return

    users_ids = [user.id for user in users]
    connected_computers = await state.get_connected_computers()

    if computer_id in connected_computers:
        connected_computers_without_current = copy.copy(connected_computers)
        del connected_computers_without_current[computer_id]
        await raise_if_users_already_connected(connected_computers_without_current, users_ids)

        computer = connected_computers[computer_id]
        if computer.status != EventStatus.NOT_STARTED:
            if users_ids != computer.users_ids:
                raise Exception("You can't change users_ids during session")

        connected_computer_edit = ConnectedComputerEdit(id=computer_id, users_ids=users_ids, is_connected=True)
        await state.edit_connected_computer(connected_computer_edit)

        logger.info(f'computer_id:{computer_id} was reconnected. is_teacher={is_teacher}. users_ids={users_ids}')
    else:
        await raise_if_users_already_connected(connected_computers, users_ids)
        connected_computer = ConnectedComputer(users_ids=users_ids, id=computer_id, is_connected=True)
        await state.add_connected_computer(connected_computer)

        logger.info(f'computer_id:{computer_id} was connected. is_teacher={is_teacher}. users_ids={users_ids}')

    await broadcast_connected_computers()
