from typing import Dict, Optional

from fastapi import WebSocketDisconnect

from schemas import ConnectedComputer, Lesson, ConnectedComputerEdit, EventStatus
from services.connection_manager import ConnectionManager


class State:
    lesson: Optional[Lesson] = None
    connected_computers: Dict[int, ConnectedComputer] = {}
    manager = ConnectionManager()

    @staticmethod
    def add_connected_computer(connected_computer: ConnectedComputer):
        State.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    def edit_connected_computer(connected_computer_edit: ConnectedComputerEdit):
        edited_data = connected_computer_edit.dict(exclude_unset=True)
        computer = State.connected_computers[connected_computer_edit.id]

        for field, value in edited_data.items():
            setattr(computer, field, value)

    @staticmethod
    def remove_connected_computer(computer_id: int):
        del State.connected_computers[computer_id]

    def clean_connected_computers(self):
        """Cleans only types and modes, but it is still connected"""
        # TODO: THINK! Maybe I need to disconnect everyone
        for computer_id, computer in State.connected_computers.items():
            computer.event_type = None
            computer.event_mode = None
            computer.status = EventStatus.NOT_STARTED.value
            computer.step = None

    @staticmethod
    async def users_exit(computer_id: int, payload: dict, *_args, **kwargs):
        # Ids выходящих юзеров
        users_ids = payload.get('users_ids')
        computer = State.connected_computers[computer_id]

        for user_id in users_ids:
            if user_id in computer.users_ids:
                computer.users_ids.remove(user_id)

        if not computer.users_ids:
            State.remove_connected_computer(computer_id)
            ws = kwargs.get('ws')
            await ws.close()
            raise WebSocketDisconnect
        else:
            computer_edit = ConnectedComputerEdit(id=computer_id, users_ids=computer.users_ids)
            State.edit_connected_computer(computer_edit)


state = State()