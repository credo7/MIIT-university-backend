from typing import List, Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: Any):
        for connection in self.active_connections:
            await connection.send_json(message)

    async def safe_broadcast(self, message: Any):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                pass
