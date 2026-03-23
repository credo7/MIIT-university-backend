import asyncio
import logging
import time
from copy import deepcopy

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.state import WebsocketServiceState
from schemas import ConnectedComputer, ConnectedComputerUpdate
from services.oauth2 import extract_ws_info_raise_if_teacher

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')


@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    try:
        users = await extract_ws_info_raise_if_teacher(ws.headers)

        connected_computers = deepcopy(WebsocketServiceState.connected_computers)
        for cmp_id, computer in connected_computers.items():
            if cmp_id == computer_id:
                continue
            for user in users:
                if user.id not in computer.users_ids:
                    continue
                if not computer.is_connected:
                    await WebsocketServiceState.remove_connected_computer(cmp_id)
                else:
                    await ws.close(code=1008, reason=f'{user.last_name} {user.first_name} уже подключен к компьютеру #{cmp_id}')
                    return

        if WebsocketServiceState.is_computer_connected(computer_id):
            await ws.close(code=1008, reason='Компьютер уже подключен')
            return

        users_ids = [user.id for user in users]

        if WebsocketServiceState.is_computer_exists_and_same_users(computer_id, users_ids):
            computer_update = ConnectedComputerUpdate(id=computer_id, is_connected=True)
            await WebsocketServiceState.update_connected_computer(computer_update)
        else:
            connected_computer = ConnectedComputer(
                id=computer_id, users_ids=users_ids, is_connected=True, last_action=time.time()
            )
            await WebsocketServiceState.create_connected_computer(connected_computer)

        await WebsocketServiceState.accept_ws_connection_and_add_to_list_of_active_ws_connections(ws, computer_id)
        await handle_websocket_messages(ws, users, computer_id)
    except WebSocketDisconnect as exc:
        logger.debug(f"WebSocket отключен для компьютера {computer_id}")
    except Exception as exc:
        logger.error(f'Ошибка {str(exc)} Traceback: {exc}', exc_info=True)
        await WebsocketServiceState.safe_broadcast({'error': str(exc)})
    finally:
        await WebsocketServiceState.update_is_connected_on_false(computer_id)


async def handle_websocket_messages(ws: WebSocket, users, computer_id: int):
    """Обработка входящих WebSocket сообщений"""
    while True:
        try:
            message = await ws.receive_json()
            if message.get('type') == 'pong':
                if computer_id in WebsocketServiceState.connected_computers:
                    WebsocketServiceState.connected_computers[computer_id].last_pong = time.time()
                logger.debug(f"Получен pong от компьютера {computer_id}")
        except WebSocketDisconnect:
            logger.info(f"WebSocket отключен для компьютера {computer_id}")
            break
        except RuntimeError as exc:
            if 'not connected' in str(exc):
                logger.info(f"WebSocket закрыт для компьютера {computer_id}")
                break
            else:
                logger.error(
                    f'websocket|компьютер_id:{computer_id}|пользователи_ids:{[user.id for user in users]}|ошибка={str(exc)}',
                    exc_info=True,
                )
                break
        except Exception as exc:
            logger.error(
                f'websocket|компьютер_id:{computer_id}|пользователи_ids:{[user.id for user in users]}|ошибка={str(exc)}',
                exc_info=True,
            )
            break
        await asyncio.sleep(0.01)
