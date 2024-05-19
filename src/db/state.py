from typing import Dict

from fastapi import WebSocket

from schemas import ConnectedComputer


class WebsocketServiceState:
    connected_computers: Dict[int, ConnectedComputer] = {}
    active_connections: dict[int, WebSocket] = {}

    @staticmethod
    async def accept_ws_connection_and_add_to_list_of_active_ws_connections(websocket: WebSocket, computer_id: int):
        await websocket.accept()
        WebsocketServiceState.active_connections[computer_id] = websocket

    @staticmethod
    def upsert_connected_computer(connected_computer: ConnectedComputer):
        if connected_computer.id in WebsocketServiceState.connected_computers:
            existed_computer = WebsocketServiceState.connected_computers[connected_computer.id]

            # Если новые user_ids, то ставим новый стейт
            if connected_computer.users_ids != existed_computer.users_ids:
                WebsocketServiceState.connected_computers[connected_computer.id] = connected_computer
            else:
                existed_computer.event_id = connected_computer.event_id
                existed_computer.step_code = connected_computer.step_code
                existed_computer.event_mode = connected_computer.event_mode
                existed_computer.event_type = connected_computer.event_type

                # Чтоб не менять is_connected при вызове из rest api ( start_event, checkpoint )
                if connected_computer.is_connected is not None:
                    existed_computer.is_connected = connected_computer.is_connected
        else:
            WebsocketServiceState.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    async def safe_broadcast(message: any):
        for connection in WebsocketServiceState.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as exc:
                pass

    @staticmethod
    async def safe_broadcast_all_connected_computers():
        dict_connected_computers = [{key: v.dict()} for key, v in WebsocketServiceState.connected_computers.items()]
        for connection in WebsocketServiceState.active_connections.values():
            try:
                await connection.send_json(dict_connected_computers)
            except Exception as exc:
                pass

    @staticmethod
    async def update_is_connected_on_false(computer_id: int):
        WebsocketServiceState.connected_computers[computer_id].is_connected = False

    @staticmethod
    async def clean_all_connected_computers_and_active_connections():
        for ws in WebsocketServiceState.active_connections.values():
            try:
                await ws.close()
            except:
                pass
        WebsocketServiceState.active_connections = {}
        WebsocketServiceState.connected_computers = {}


state = WebsocketServiceState()
