from typing import Dict, Optional, Union

from fastapi import WebSocketDisconnect

from schemas import ConnectedComputer, Lesson, ConnectedComputerEdit, EventStatus, Step
from services.connection_manager import ConnectionManager


class State:
    connected_computers: Dict[int, ConnectedComputer] = {}
    manager = ConnectionManager()

    @staticmethod
    def add_connected_computer(connected_computer: ConnectedComputer):
        State.connected_computers[connected_computer.id] = connected_computer

    @staticmethod
    def upsert_connected_computer(connected_computer: ConnectedComputer):
        if connected_computer.id in State.connected_computers and \
                connected_computer.users_ids == State.connected_computers[connected_computer.id]:
            computer_edit = ConnectedComputerEdit(
                id=connected_computer.id,
                event_type=connected_computer.event_type,
                event_mode=connected_computer.event_mode,
                step=connected_computer.step
            )
            State.edit_connected_computer(computer_edit)
        else:
            State.add_connected_computer(connected_computer)

    @staticmethod
    def update_connected_computer_checkpoint(
            connected_computer_id: int,
            step: Optional[Union[Step, str]]
    ):
        print(f"REST CONNECTED_COMPUTERS={State.connected_computers}")
        connected_computer = State.connected_computers[connected_computer_id]
        connected_computer.step = step

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
