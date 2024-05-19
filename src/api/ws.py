""" Логика
    Студент(ы) подключа(ется/ются) к компу -> upsert connected_компьютер
    Старт работы -> если не было, то add_without_connected = True, else просто обновляем код
    Финиш работ учителя -> очищаем весь список, отправляем всем "work_finished" по WS
"""


import logging

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from handlers.raise_hand import RaiseHand
from schemas import (
    WSMessage,
    WSCommandTypes,
    ConnectedComputer,
)
from db.mongo import Database, get_db
from db.state import WebsocketServiceState
from services.oauth2 import extract_ws_info_raise_if_teacher

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')

db: Database = get_db()


ws_handlers = {
    # WSCommandTypes.FINISH: EventService(db).finish_current_lesson, ???
    WSCommandTypes.RAISE_HAND: RaiseHand(db).run,
    # WSCommandTypes.EXIT: State.users_exit,
}


# @router.websocket('/ws/{computer_id}')
# async def websocket_endpoint(ws: WebSocket, computer_id: int):
#     try:
#         is_teacher, users = extract_ws_info(ws.headers)
#
#     except Exception as exc:
#         logger.error(exc, exc_info=True)


@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    try:
        users = extract_ws_info_raise_if_teacher(ws.headers)

        connected_computer = ConnectedComputer(id=computer_id, users_ids=[user.id for user in users], is_connected=True)

        await WebsocketServiceState.accept_ws_connection_and_add_to_list_of_active_ws_connections(ws, computer_id)
        WebsocketServiceState.upsert_connected_computer(connected_computer)
        await WebsocketServiceState.safe_broadcast_all_connected_computers()

        await handle_websocket_messages(ws, users, computer_id)
    except WebSocketDisconnect as exc:
        pass
    except Exception as exc:
        logger.error(f'Error {str(exc)} Traceback: {exc}', exc_info=True)
        await WebsocketServiceState.safe_broadcast({'error': str(exc)})
    finally:
        await WebsocketServiceState.update_is_connected_on_false(computer_id)
        await WebsocketServiceState.safe_broadcast_all_connected_computers()


async def handle_websocket_messages(ws, users, computer_id):
    while True:
        message = None
        try:
            _data = await ws.receive_json()
            # message = WSMessage(**data)
            # await ws_handlers[message.type](
            #     computer_id=computer_id, payload=message.payload, ws=ws
            # )
            # logger.info(
            #     f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|type:{message.type}|succesfully'
            # )
        except WebSocketDisconnect:
            raise WebSocketDisconnect
        except Exception as exc:
            logger.error(
                f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|'
                # f'type:{message.type if message is not None else message}'
                f'|err={str(exc)}',
                exc_info=True,
            )
        finally:
            await asyncio.sleep(0.01)
