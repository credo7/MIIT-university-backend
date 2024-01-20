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
from db.state import state
from services.event import EventService
from services.oauth2 import extract_ws_info
from services.ws import connect_with_broadcast, disconnect, broadcast_connected_computers

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')

db: Database = get_db()


ws_handlers = {
    WSCommandTypes.SELECT_TYPE: actualize_computer_state,
    WSCommandTypes.START: StartEvents(state, state.manager, db).run,
    WSCommandTypes.FINISH: EventService(state, db).finish_current_lesson,
    WSCommandTypes.RAISE_HAND: RaiseHand(state, db).run,
    WSCommandTypes.EXIT: state.users_exit,
}


@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    is_teacher, users = False, []
    try:
        is_teacher, users = await extract_ws_info(ws.headers)
        await connect_with_broadcast(ws, users, computer_id, is_teacher)
        await handle_websocket_messages(ws, users, computer_id, is_teacher)
    except WebSocketDisconnect as exc:
        pass
    except Exception as exc:
        logger.error(f'Error {str(exc)} Traceback: {exc}', exc_info=True)
        await state.manager.safe_broadcast({'error': str(exc)})
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
            logger.info(f'ws|cid:{computer_id}|uids:{[user.id for user in users]}|type:{message.type}|succesfully')
        except WebSocketDisconnect:
            raise WebSocketDisconnect
        except Exception as exc:
            logger.error(
                f'ws|cid:{computer_id}|uids:{[user.id for user in users]}|type:{message.type}|err={str(exc)}',
                exc_info=True,
            )
