import json
from typing import Dict, Optional

import aioredis
from fastapi import WebSocketDisconnect

from core.config import settings
from schemas import ConnectedComputer, Lesson, ConnectedComputerEdit, EventStatus
from services.connection_manager import ConnectionManager


class State:
    def __init__(self):
        self.r = aioredis.from_url(settings.redis_url)
        self.manager = ConnectionManager()

    async def get_lesson(self) -> Optional[Lesson]:
        raw_lesson = await self.r.get("current_lesson")
        if raw_lesson is None:
            return None
        lesson_dict = json.loads(raw_lesson)
        return Lesson(**lesson_dict)

    async def set_lesson(self, lesson: Lesson) -> None:
        lesson_dict = lesson.dict()
        dumped_lesson = json.dumps(lesson_dict, default=str)
        await self.r.set("current_lesson", dumped_lesson)

    async def get_connected_computers(self) -> Dict[int, ConnectedComputer]:
        raw_connected_computers = await self.r.get("connected_computers")
        connected_computers_dict = json.loads(raw_connected_computers) if raw_connected_computers else {}

        connected_computers: Dict[int, ConnectedComputer] = {}
        for key, computer in connected_computers_dict.items():
            connected_computers[int(key)] = ConnectedComputer(**computer)

        return connected_computers

    async def set_connected_computers(self, connected_computers: Dict[int, ConnectedComputer]) -> None:
        connected_computers_dict = {}
        for key, value in connected_computers.items():
            connected_computers_dict[key] = value.dict()
        dumped_connected_computers = json.dumps(connected_computers_dict)
        await self.r.set("connected_computers", dumped_connected_computers)

    async def add_connected_computer(self, connected_computer: ConnectedComputer):
        connected_computers = await self.get_connected_computers()
        connected_computers[connected_computer.id] = connected_computer
        await self.set_connected_computers(connected_computers)

    async def edit_connected_computer(self, connected_computer_edit: ConnectedComputerEdit):
        connected_computers = await self.get_connected_computers()
        edited_data = connected_computer_edit.dict(exclude_unset=True)
        computer = connected_computers[connected_computer_edit.id]

        for field, value in edited_data.items():
            setattr(computer, field, value)

        await self.set_connected_computers(connected_computers)

    async def remove_connected_computer(self, computer_id: int):
        connected_computers = await self.get_connected_computers()
        if computer_id in connected_computers:
            del connected_computers[computer_id]
        await self.set_connected_computers(connected_computers)

    async def clean_connected_computers(self):
        """Cleans only types and modes, but it is still connected"""
        connected_computers = await self.get_connected_computers()
        for computer_id, computer in connected_computers.items():
            computer.event_type = None
            computer.event_mode = None
            computer.status = EventStatus.NOT_STARTED.value
            computer.step = None
        await self.set_connected_computers(connected_computers)

    async def users_exit(self, computer_id: int, payload: dict, *_args, **kwargs):
        connected_computers = await self.get_connected_computers()
        # Ids выходящих юзеров
        users_ids = payload.get("users_ids")
        computer = connected_computers[computer_id]

        for user_id in users_ids:
            if user_id in computer.users_ids:
                computer.users_ids.remove(user_id)

        if not computer.users_ids:
            await self.remove_connected_computer(computer_id)
            ws = kwargs.get("ws")
            await ws.close()
            raise WebSocketDisconnect
        else:
            computer_edit = ConnectedComputerEdit(id=computer_id, users_ids=computer.users_ids)
            await self.edit_connected_computer(computer_edit)


state = State()
