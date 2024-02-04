import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from handlers.actualize_computer_state import actualize_computer_state
from handlers.raise_hand import RaiseHand
from handlers.start_events import StartEvents
from schemas import (
    WSMessage,
    WSCommandTypes,
)
from db.mongo import Database, get_db
from db.state import State
from services.event import EventService
from services.oauth2 import extract_ws_info
from services.ws import connect_with_broadcast, disconnect, broadcast_connected_computers

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')

db: Database = get_db()


ws_handlers = {
    WSCommandTypes.SELECT_TYPE: actualize_computer_state,
    WSCommandTypes.START: StartEvents(db).run,
    WSCommandTypes.FINISH: EventService(db).finish_current_lesson,
    WSCommandTypes.RAISE_HAND: RaiseHand(db).run,
    WSCommandTypes.EXIT: State.users_exit,
}


@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    is_teacher, users = False, []
    try:
        if ws.headers.get('broadcast_connected_computers', False):
            await broadcast_connected_computers()
            return
        is_teacher, users = extract_ws_info(ws.headers)
        await connect_with_broadcast(ws, users, computer_id, is_teacher)
        await handle_websocket_messages(ws, users, computer_id, is_teacher)
    except WebSocketDisconnect as exc:
        pass
    except Exception as exc:
        logger.error(f'Error {str(exc)} Traceback: {exc}', exc_info=True)
        await State.manager.safe_broadcast({'error': str(exc)})
    finally:
        await disconnect(ws, computer_id, is_teacher, [user.id for user in users])
        await broadcast_connected_computers()


async def handle_websocket_messages(ws, users, computer_id, is_teacher):
    while True:
        message = None
        try:
            data = await ws.receive_json()
            message = WSMessage(**data)
            await ws_handlers[message.type](
                computer_id=computer_id, payload=message.payload, is_teacher=is_teacher, ws=ws
            )
            logger.info(
                f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|type:{message.type}|succesfully'
            )
        except WebSocketDisconnect:
            print('DISCONECT')
            raise WebSocketDisconnect
        except Exception as exc:
            logger.error(
                f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|type:{message.type}|err={str(exc)}',
                exc_info=True,
            )
