import asyncio
import logging
from fastapi.websockets import WebSocket

from schemas import ConnectedComputer, ConnectedComputerUpdate

logger = logging.getLogger(__name__)


class WebsocketServiceState:
    connected_computers: dict[int, ConnectedComputer] = {}
    active_connections: dict[int, WebSocket] = {}
    lock = asyncio.Lock()

    @staticmethod
    def is_user_connected(user_id: str) -> int:
        for computer_id, computer in WebsocketServiceState.connected_computers.items():
            if user_id in computer.users_ids:
                return computer_id
        return -1

    @staticmethod
    async def accept_ws_connection_and_add_to_list_of_active_ws_connections(websocket: WebSocket, computer_id: int):
        await websocket.accept()
        async with WebsocketServiceState.lock:
            WebsocketServiceState.active_connections[computer_id] = websocket
            logger.info(f"WebSocket connected for computer {computer_id}")

    @staticmethod
    async def remove_connected_computer(computer_id: int):
        async with WebsocketServiceState.lock:
            WebsocketServiceState.connected_computers.pop(computer_id, None)

    @staticmethod
    async def create_connected_computer(connected_computer: ConnectedComputer):
        async with WebsocketServiceState.lock:
            WebsocketServiceState.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    async def update_connected_computer(connected_computer: ConnectedComputerUpdate):
        async with WebsocketServiceState.lock:
            if connected_computer.id in WebsocketServiceState.connected_computers:
                existing_computer = WebsocketServiceState.connected_computers[connected_computer.id]
                update_data = {k: v for k, v in vars(connected_computer).items() if v is not None}
                existing_computer.__dict__.update(update_data)
                return True  # Update successful
            return False  # ID not found

    @staticmethod
    async def safe_broadcast(message: any):
        async with WebsocketServiceState.lock:
            for computer_id, connection in list(WebsocketServiceState.active_connections.items()):
                try:
                    await connection.send_json(message)
                except Exception as exc:
                    logger.error(f"Error sending message to {computer_id}: {exc}")
                    del WebsocketServiceState.active_connections[computer_id]  # Remove broken WebSocket

    @staticmethod
    async def safe_broadcast_all_connected_computers(self):
        """Send all connected computers' data to active WebSocket clients."""
        async with WebsocketServiceState.lock:
            dict_connected_computers = {key: v.dict() for key, v in WebsocketServiceState.connected_computers.items()}
            for computer_id, connection in list(WebsocketServiceState.active_connections.items()):
                try:
                    await connection.send_json(dict_connected_computers)
                except Exception as exc:
                    logger.error(f"Error sending connected computers to {computer_id}: {exc}")
                    del WebsocketServiceState.active_connections[computer_id]  # Remove failed WebSocket

    @staticmethod
    async def update_is_connected_on_false(computer_id: int):
        """Mark a computer as disconnected in the state."""
        async with WebsocketServiceState.lock:
            if computer_id in WebsocketServiceState.connected_computers:
                WebsocketServiceState.connected_computers[computer_id].is_connected = False
                logger.info(f"Computer {computer_id} marked as disconnected")

    @staticmethod
    async def clean_all_connected_computers_and_active_connections(self):
        """Close all WebSocket connections and clear the state."""
        async with WebsocketServiceState.lock:
            for computer_id, ws in list(WebsocketServiceState.active_connections.items()):
                try:
                    await ws.close()
                    logger.info(f"WebSocket for {computer_id} closed successfully")
                except Exception as e:
                    logger.warning(f"Failed to close WebSocket for {computer_id}: {e}")
                finally:
                    del WebsocketServiceState.active_connections[computer_id]  # Ensure removal even if error occurs

            WebsocketServiceState.connected_computers.clear()
            logger.info("All connected computers and active WebSocket connections cleared.")

    @staticmethod
    def is_computer_connected(computer_id: int) -> bool:
        if computer_id in WebsocketServiceState.connected_computers and WebsocketServiceState.connected_computers[computer_id].is_connected:
            return True
        return False

    @staticmethod
    def is_computer_exists_and_same_users(computer_id: int, users_ids: list[str]) -> bool:
        if computer_id not in WebsocketServiceState.connected_computers:
            print("==================================")
            print(f"computer_id={computer_id}")
            print(f"WebsocketServiceState.connected_computers={WebsocketServiceState.connected_computers}")
            print("==================================")
            return False
        if users_ids == WebsocketServiceState.connected_computers[computer_id].users_ids:
            print(f"users_ids={users_ids}")
            print(f"WebsocketServiceState.connected_computers[computer_id].users_ids={WebsocketServiceState.connected_computers[computer_id].users_ids}")
            return True
        print("DIFFERENT COMPUTER USERS")
        return False
