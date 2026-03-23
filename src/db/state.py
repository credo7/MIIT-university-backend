import asyncio
import logging
import time
from typing import Any, Dict

from fastapi import WebSocket

from schemas import ConnectedComputer, ConnectedComputerUpdate

logger = logging.getLogger(__name__)


class WebsocketServiceState:
    connected_computers: dict[int, ConnectedComputer] = {}
    active_connections: dict[int, WebSocket] = {}

    @staticmethod
    def is_user_connected(user_id: str) -> int:
        """Проверить подключен ли пользователь"""
        for computer_id, computer in WebsocketServiceState.connected_computers.items():
            if computer.is_connected and user_id in computer.users_ids:
                return computer_id
        return -1

    @staticmethod
    async def remove_connected_computer(computer_id: int):
        """Удаление отключенного компьютера из состояния"""
        WebsocketServiceState.connected_computers.pop(computer_id, None)
        WebsocketServiceState.active_connections.pop(computer_id, None)
        logger.info(f"Компьютер {computer_id} удален из активных подключений")

    @staticmethod
    async def update_is_connected_on_false(computer_id: int):
        """Пометить компьютер как отключенный (установить is_connected в False)"""
        if computer_id in WebsocketServiceState.connected_computers:
            update_computer = ConnectedComputerUpdate(id=computer_id, is_connected=False)
            await WebsocketServiceState.update_connected_computer(update_computer)
            logger.info(f"Компьютер {computer_id} помечен как отключенный")

    @staticmethod
    async def accept_ws_connection_and_add_to_list_of_active_ws_connections(websocket: WebSocket, computer_id: int):
        """Принять WebSocket соединение и добавить в список активных подключений"""
        await websocket.accept()
        WebsocketServiceState.active_connections[computer_id] = websocket
        logger.info(f"WebSocket подключен для компьютера {computer_id}")

        loop = asyncio.get_running_loop()
        loop.create_task(WebsocketServiceState.ping_pong_task(computer_id, websocket))

    @staticmethod
    async def ping_pong_task(computer_id: int, websocket: WebSocket):
        """Фоновая задача для отправки ping и проверки активности соединения"""
        try:
            while True:
                await asyncio.sleep(10)
                ping_message = {"type": "ping"}
                await websocket.send_json(ping_message)
                logger.debug(f"Отправлен ping компьютеру {computer_id}")

                computer = WebsocketServiceState.connected_computers.get(computer_id)
                if computer is None:
                    break

                if time.time() - getattr(computer, "last_pong", time.time()) > 30 and computer.is_connected and time.time() - computer.last_action > 30:
                    logger.warning(f"Не получен pong от компьютера {computer_id}. Помечаем как отключенный")
                    await WebsocketServiceState.mark_as_disconnected(computer_id)
                    await websocket.close()
                    WebsocketServiceState.active_connections.pop(computer_id, None)
                    break
        except Exception as e:
            logger.error(f"Ошибка в задаче ping-pong для компьютера {computer_id}: {e}")

    @staticmethod
    async def mark_as_disconnected(computer_id: int):
        """Пометить компьютер как отключенный вместо немедленного удаления"""
        if computer_id in WebsocketServiceState.connected_computers:
            update_computer = ConnectedComputerUpdate(id=computer_id, is_connected=False)
            await WebsocketServiceState.update_connected_computer(update_computer)
            logger.info(f"Компьютер {computer_id} помечен как отключенный")

    @staticmethod
    async def create_connected_computer(connected_computer: ConnectedComputer):
        """Создание записи о подключенном компьютере"""
        WebsocketServiceState.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    async def update_connected_computer(connected_computer: ConnectedComputerUpdate):
        """Обновление информации о подключенном компьютере"""
        if connected_computer.id in WebsocketServiceState.connected_computers:
            existing_computer = WebsocketServiceState.connected_computers[connected_computer.id]
            update_data = {k: v for k, v in vars(connected_computer).items() if v is not None}
            existing_computer.__dict__.update(update_data)
            return True
        return False

    @staticmethod
    async def safe_broadcast(message: Dict[str, Any]):
        """Отправка сообщения всем активным WebSocket соединениям"""
        for computer_id, connection in list(WebsocketServiceState.active_connections.items()):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error(f"Ошибка отправки сообщения на {computer_id}: {exc}")
                del WebsocketServiceState.active_connections[computer_id]

    @staticmethod
    async def clean_expired_computers():
        """Периодическое удаление устаревших отключенных компьютеров"""
        while True:
            await asyncio.sleep(60)
            expired_computers = []
            for computer_id, computer in list(WebsocketServiceState.connected_computers.items()):
                if not computer.is_connected and computer.is_expired():
                    expired_computers.append(computer_id)
            for computer_id in expired_computers:
                del WebsocketServiceState.connected_computers[computer_id]
                logger.info(f"Удален устаревший отключенный компьютер {computer_id}")
            if expired_computers:
                logger.info(f"Очистка завершена. Удалено {len(expired_computers)} компьютеров")

    @staticmethod
    def is_computer_connected(computer_id: int) -> bool:
        """Проверить подключен ли компьютер"""
        return computer_id in WebsocketServiceState.connected_computers and WebsocketServiceState.connected_computers[computer_id].is_connected

    @staticmethod
    def is_computer_exists_and_same_users(computer_id: int, users_ids: list[str]) -> bool:
        """Проверить существует ли компьютер с такими же пользователями"""
        return computer_id in WebsocketServiceState.connected_computers and users_ids == WebsocketServiceState.connected_computers[computer_id].users_ids