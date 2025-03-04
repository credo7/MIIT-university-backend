import asyncio
import logging
import time
from copy import deepcopy

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException

from db.state import WebsocketServiceState
from schemas import ConnectedComputer, ConnectedComputerUpdate
from db.mongo import Database, get_db
from services.oauth2 import extract_ws_info_raise_if_teacher

logger = logging.getLogger(__name__)

router = APIRouter(tags=['ws'], prefix='')

db: Database = get_db()

@router.websocket('/ws/{computer_id}')
async def websocket_endpoint(ws: WebSocket, computer_id: int):
    try:
        users = extract_ws_info_raise_if_teacher(ws.headers)

        # Check if any computer already has these users
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
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{user.last_name} {user.first_name} уже подключен к компьютеру #{cmp_id}"
                    )

        print(f"WebsocketServiceState.connected_computers={WebsocketServiceState.connected_computers}")
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

        # Accept connection and add to active connections.
        await WebsocketServiceState.accept_ws_connection_and_add_to_list_of_active_ws_connections(ws, computer_id)
        await handle_websocket_messages(ws, users, computer_id)
    except WebSocketDisconnect as exc:
        pass
    except Exception as exc:
        logger.error(f'Error {str(exc)} Traceback: {exc}', exc_info=True)
        await WebsocketServiceState.safe_broadcast({'error': str(exc)})
    finally:
        await WebsocketServiceState.update_is_connected_on_false(computer_id)


async def handle_websocket_messages(ws: WebSocket, users, computer_id: int):
    while True:
        try:
            message = await ws.receive_json()
            # Check if this is a pong message
            if message.get("type") == "pong":
                if computer_id in WebsocketServiceState.connected_computers:
                    WebsocketServiceState.connected_computers[computer_id].last_pong = time.time()
                    # print(f"IN HANDLE {WebsocketServiceState.connected_computers[computer_id].last_pong}")
                # logger.info(f"✅ Received Pong from computer {computer_id}")
            else:
                # Custom handling for other message types
                ...
                # logger.info(f"📩 Received message from computer {computer_id}: {message}")
        except WebSocketDisconnect:
            # logger.info(f"WebSocket disconnected for computer {computer_id}. Exiting loop.")
            break
        except RuntimeError as exc:
            # Check if the error is because the WebSocket is closed
            if "not connected" in str(exc):
                # logger.info(f"WebSocket closed for computer {computer_id}. Exiting loop.")
                break
            else:
                logger.error(
                    f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|err={str(exc)}',
                    exc_info=True,
                )
                break
        except Exception as exc:
            logger.error(
                f'websocket|computer_id:{computer_id}|user_ids:{[user.id for user in users]}|err={str(exc)}',
                exc_info=True,
            )
            break
        await asyncio.sleep(0.01)

