import asyncio
import logging
import time

from fastapi import WebSocket
from schemas import ConnectedComputer, ConnectedComputerUpdate

logger = logging.getLogger(__name__)



class WebsocketServiceState:
    connected_computers: dict[int, ConnectedComputer] = {}
    active_connections: dict[int, WebSocket] = {}
    # lock = asyncio.Lock()

    @staticmethod
    def is_user_connected(user_id: str) -> int:
        for computer_id, computer in WebsocketServiceState.connected_computers.items():
            if computer.is_connected and user_id in computer.users_ids:
                return computer_id
        return -1

    @staticmethod
    async def remove_connected_computer(computer_id: int):
        """Remove a disconnected computer from the state."""
        # async with WebsocketServiceState.lock:
        WebsocketServiceState.connected_computers.pop(computer_id, None)
        WebsocketServiceState.active_connections.pop(computer_id, None)
        logger.info(f"❌ Computer {computer_id} removed from active connections.")

    @staticmethod
    async def update_is_connected_on_false(computer_id: int):
        """Mark a computer as disconnected (set is_connected to False)."""
        # async with WebsocketServiceState.lock:
        if computer_id in WebsocketServiceState.connected_computers:
            update_computer = ConnectedComputerUpdate(id=computer_id, is_connected=False)
            await WebsocketServiceState.update_connected_computer(update_computer)
            logger.info(f"🚫 Computer {computer_id} marked as disconnected")

    @staticmethod
    async def accept_ws_connection_and_add_to_list_of_active_ws_connections(websocket: WebSocket, computer_id: int):
        await websocket.accept()
        # async with WebsocketServiceState.lock:
        WebsocketServiceState.active_connections[computer_id] = websocket
        logger.info(f"WebSocket connected for computer {computer_id}")

        # Use the current running loop to create the background task.
        loop = asyncio.get_running_loop()
        loop.create_task(WebsocketServiceState.ping_pong_task(computer_id, websocket))

    @staticmethod
    async def ping_pong_task(computer_id: int, websocket: WebSocket):
        """Background task to send pings and check if the connection is still alive."""
        try:
            while True:
                print("in ping_pong_task")
                await asyncio.sleep(10)  # Send a ping every 20 seconds
                ping_message = {"type": "ping"}
                await websocket.send_json(ping_message)
                logger.info(f"🔄 Sent Ping to computer {computer_id}")

                # Check if a recent pong was received by comparing timestamps.
                # async with WebsocketServiceState.lock:
                computer = WebsocketServiceState.connected_computers.get(computer_id)
                if computer is None:
                    break  # The computer entry was removed.
                # Assume computer.last_pong is maintained elsewhere (e.g., in your receive loop).
                print(f"IN ping_pong_task last_pong = {computer.last_pong}")
                if time.time() - getattr(computer, "last_pong", time.time()) > 30 and computer.is_connected and time.time() - computer.last_action > 30:
                    logger.warning(f"❌ No recent Pong received from computer {computer_id}. Marking as disconnected.")
                    await WebsocketServiceState.mark_as_disconnected(computer_id)
                    await websocket.close()
                    WebsocketServiceState.active_connections.pop(computer_id, None)
                    break
        except Exception as e:
            logger.error(f"⚠️ Error in Ping-Pong task for computer {computer_id}: {e}")

    @staticmethod
    async def mark_as_disconnected(computer_id: int):
        """Mark a computer as disconnected instead of removing it immediately."""
        # async with WebsocketServiceState.lock:
        if computer_id in WebsocketServiceState.connected_computers:
            update_computer = ConnectedComputerUpdate(id=computer_id, is_connected=False)
            await WebsocketServiceState.update_connected_computer(update_computer)
            logger.info(f"🚫 Computer {computer_id} marked as disconnected")

    @staticmethod
    async def create_connected_computer(connected_computer: ConnectedComputer):
        # async with WebsocketServiceState.lock:
        WebsocketServiceState.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    async def update_connected_computer(connected_computer: ConnectedComputerUpdate):
        # async with WebsocketServiceState.lock:
        if connected_computer.id in WebsocketServiceState.connected_computers:
            existing_computer = WebsocketServiceState.connected_computers[connected_computer.id]
            update_data = {k: v for k, v in vars(connected_computer).items() if v is not None}
            existing_computer.__dict__.update(update_data)
            return True  # Update successful
        return False  # ID not found

    @staticmethod
    async def safe_broadcast(message: any):
        """Broadcast message to all active WebSocket connections."""
        # async with WebsocketServiceState.lock:
        for computer_id, connection in list(WebsocketServiceState.active_connections.items()):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error(f"Error sending message to {computer_id}: {exc}")
                del WebsocketServiceState.active_connections[computer_id]  # Remove broken connection

    @staticmethod
    async def clean_expired_computers():
        """Periodically remove expired disconnected computers."""
        while True:
            print(f"in clean_expired_computers", flush=True)
            await asyncio.sleep(60)  # Run every 60 seconds
            # async with WebsocketServiceState.lock:
            expired_computers = []
            for computer_id, computer in list(WebsocketServiceState.connected_computers.items()):
                if not computer.is_connected and computer.is_expired():
                    expired_computers.append(computer_id)
            for computer_id in expired_computers:
                del WebsocketServiceState.connected_computers[computer_id]
                logger.info(f"🗑️ Removed expired disconnected computer {computer_id}")
            logger.info(f"🧹 Cleanup complete. Removed {len(expired_computers)} computers.")

    @staticmethod
    def is_computer_connected(computer_id: int) -> bool:
        return computer_id in WebsocketServiceState.connected_computers and WebsocketServiceState.connected_computers[computer_id].is_connected

    @staticmethod
    def is_computer_exists_and_same_users(computer_id: int, users_ids: list[str]) -> bool:
        return computer_id in WebsocketServiceState.connected_computers and users_ids == WebsocketServiceState.connected_computers[computer_id].users_ids

# Note: Do not call create_task() at the module level. Instead, ensure that any background tasks (like clean_expired_computers)
# are scheduled in a startup event in your FastAPI app.