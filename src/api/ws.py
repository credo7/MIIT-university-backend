""" Логика
    Студент(ы) подключа(ется/ются) к компу -> upsert connected_компьютер
    Старт работы -> если не было, то add_without_connected = True, else просто обновляем код
    Финиш работ учителя -> очищаем весь список, отправляем всем "work_finished" по WS
"""


import logging

import asyncio
import time
from copy import deepcopy

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException

from schemas import ConnectedComputer, ConnectedComputerUpdate
from db.mongo import Database, get_db
from db.state import WebsocketServiceState
from services.oauth2 import extract_ws_info_raise_if_teacher

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')

db: Database = get_db()

@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    try:
        users = extract_ws_info_raise_if_teacher(ws.headers)

        connected_computers = deepcopy(WebsocketServiceState.connected_computers)
        for computer_id, computer in connected_computers.items():
            if computer_id == computer_id:
                continue
            for user in users:
                if user.id not in computer.users_ids:
                    continue
                if not computer.is_connected:
                    await WebsocketServiceState.remove_connected_computer(computer_id)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{user.last_name} {user.first_name} уже подключен к компьютеру #{computer_id}"
                    )

        if WebsocketServiceState.is_computer_connected(computer_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Компьютер уже подключен"
            )

        users_ids = [user.id for user in users]

        if WebsocketServiceState.is_computer_exists_and_same_users(computer_id, users_ids):
            print("is_computer_exists_and_same_users = TRUE")
            computer_update = ConnectedComputerUpdate(
                id=computer_id,
                is_connected=True
            )
            await WebsocketServiceState.update_connected_computer(computer_update)
        else:
            print("is_computer_exists_and_same_users = FALSE")
            connected_computer = ConnectedComputer(
                id=computer_id,
                users_ids=users_ids,
                is_connected=True,
                last_action=time.time()
            )
            await WebsocketServiceState.create_connected_computer(connected_computer)

        await WebsocketServiceState.accept_ws_connection_and_add_to_list_of_active_ws_connections(ws, computer_id)
        await handle_websocket_messages(ws, users, computer_id)
    except WebSocketDisconnect as exc:
        pass
    except Exception as exc:
        logger.error(f'Error {str(exc)} Traceback: {exc}', exc_info=True)
        await WebsocketServiceState.safe_broadcast({'error': str(exc)})
    finally:
        await WebsocketServiceState.update_is_connected_on_false(computer_id)


async def handle_websocket_messages(ws, users, computer_id):
    while True:
        message = None
        try:
            _data = await ws.receive_json()
        except WebSocketDisconnect:
            raise WebSocketDisconnect
        except Exception as exc:
            logger.error(
                f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|'
                f'|err={str(exc)}',
                exc_info=True,
            )
        finally:
            await asyncio.sleep(0.01)
