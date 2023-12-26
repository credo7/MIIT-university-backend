import json
from typing import Dict

import aioredis

from core.config import settings
from schemas import ConnectedComputer, Lesson, ConnectedComputerEdit


class State:
    def __init__(self):
        self.r = aioredis.from_url(settings.redis_url)

    async def get_lesson(self) -> Lesson:
        raw_lesson = await self.r("current_lesson")
        lesson_dict = json.loads(raw_lesson)
        return Lesson(**lesson_dict)

    async def set_lesson(self, lesson: Lesson) -> None:
        await self.r.set("current_lesson", lesson.dict())

    async def get_connected_computers(self) -> Dict[int, ConnectedComputer]:
        raw_connected_computers = await self.r.get("connected_computers")
        connected_computers_dict = json.loads(raw_connected_computers)

        connected_computers: Dict[int, ConnectedComputer] = {}
        for key, computer in connected_computers_dict.items():
            connected_computers[key] = ConnectedComputer(**computer)

        return connected_computers
    async def set_connected_computers(self, connected_computers: Dict[int, ConnectedComputer]) -> None:
        await self.r.set("connected_computers", connected_computers)

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


state = State()
