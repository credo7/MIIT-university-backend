from typing import Dict, Any, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from handlers.start_events import StartEvents
from schemas import WSMessage, WSCommandTypes, ConnectedComputer, ConnectedComputerEdit
from services.connection_manager import ConnectionManager
from db.mongo import Database, get_db
from db.state import state


router = APIRouter(tags=['ws'], prefix='')

manager = ConnectionManager()

db: Database = get_db()


async def broadcast_connected_computers():
    connected_computers = await state.get_connected_computers()
    dict_connected_computers = [{key: v.dict()} for key, v in connected_computers.items()]
    await manager.broadcast(dict_connected_computers)


async def disconnect(computer_id: int, error: Optional[Dict] = None):
    await update_computer_status(computer_id, False)
    await broadcast_connected_computers()
    if error is not None:
        await manager.broadcast(error)


async def raise_if_users_connected(users_ids: List[str]):
    """Проверяем студентов на уникальность, может он уже подключен к другому компьютеру"""
    connected_computers = await state.get_connected_computers()
    for computer_id, connected_computer in connected_computers.items():
        for user_id in users_ids:
            if user_id in connected_computer.users_ids:
                raise Exception(f"Студент с user_id {user_id} уже подключен за компьтер с номером {computer_id}")


async def actualize_computer_state(computer_id: int, payload: Any):
    connected_computer = ConnectedComputer(**payload, computer_id=computer_id, is_connected=True, is_started=False)
    await raise_if_users_connected(connected_computer.users_ids)
    state.add_connected_computer(connected_computer)
    await broadcast_connected_computers()


async def update_computer_status(computer_id: int, is_connected: bool = True):
    # Если компьютер уже был подключен, то активируем статус коннектед и броадкастим и наоборот
    await state.edit_connected_computer(ConnectedComputerEdit(id=computer_id, is_connected=is_connected))
    await broadcast_connected_computers()


async def connect_with_broadcast(websocket: WebSocket, computer_id: int):
    await manager.connect(websocket)
    await update_computer_status(computer_id)


ws_handlers = {
    WSCommandTypes.SELECT_TYPE: actualize_computer_state,
    WSCommandTypes.START: StartEvents(state, manager, db).run
}


@router.websocket("/ws/{computer_id}")
async def websocket_endpoint(websocket: WebSocket, computer_id: int):
    # TODO: token = websocket.headers.get("HTTP_AUTHORIZATION")
    await connect_with_broadcast(websocket, computer_id)
    while True:
        try:
            data = await websocket.receive_json()
            message = WSMessage(**data)
            await ws_handlers[message.type](computer_id, message.payload)
        except WebSocketDisconnect:
            await disconnect(computer_id, {"type": "ERROR", "payload": "Disconnected"})
        except Exception as err:
            await disconnect(computer_id, {"type": "ERROR", "payload": str(err)})
