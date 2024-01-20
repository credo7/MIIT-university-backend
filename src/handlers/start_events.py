import random
from typing import List

from bson import ObjectId

from pymongo.database import Database

from db.mongo import CollectionNames
from db.state import State
from schemas import (
    Lesson,
    EventType,
    EventInfo,
    EventStatus,
    ConnectedComputerEdit,
    EventMode,
    ConnectedComputer,
)
from services.connection_manager import ConnectionManager
from services.event import EventService
from services.practice_one import PracticeOne
from services.utils import to_db


class StartEvents:
    def __init__(self, state: State, manager: ConnectionManager, db: Database):
        self.state = state
        self.manager = manager
        self.db = db
        self.event_service = EventService(self.state, db=self.db)

    async def run(self, is_teacher, *_args, **_kwargs):
        if not is_teacher:
            raise Exception('Только учитель может запускать работу. Чекается по токену первого юзера')
        lesson = await self.state.get_lesson()
        if lesson is not None:
            await self.event_service.finish_current_lesson()
        await self.remove_disconnected_computers()
        await self.validate()

        lesson: Lesson = await self.create_and_set_lesson()

        events = await self.generate_events(lesson)
        await to_db(events, CollectionNames.EVENTS.value)
        await self.manager.broadcast({'type': 'STATUS', 'payload': 'START'})
        await self.set_started_status(events)

    async def set_started_status(self, events: List[EventInfo]):
        for event in events:
            edit_connected_computer = ConnectedComputerEdit(id=event.computer_id, status=EventStatus.STARTED.value)
            await self.state.edit_connected_computer(edit_connected_computer)

    async def validate(self):
        await self.computers_exist()
        await self.type_and_mode_set()
        await self.identical_mode()

    async def create_and_set_lesson(self) -> Lesson:
        connected_computers = await self.state.get_connected_computers()
        conn_computer = list(connected_computers.values())[0]
        user = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(conn_computer.users_ids[0])})
        group_id = user['group_id']
        group_name = user['group_name']
        event_type = conn_computer.event_type
        event_mode = conn_computer.event_mode

        lesson = Lesson(group_id=group_id, group_name=group_name, event_type=event_type, event_mode=event_mode,)

        id = await to_db(lesson.dict(), CollectionNames.LESSONS.value)

        lesson.id = id

        await self.state.set_lesson(lesson)

        return lesson

    async def generate_events(self, lesson: Lesson):
        events = []

        connected_computers = await self.state.get_connected_computers()
        for computer_id, connected_computer in connected_computers.items():
            variant = await self.get_variant(lesson, computer_id, connected_computer)
            events.append(variant)

        return events

    async def get_variant(self, lesson: Lesson, computer_id: int, connected_computer: ConnectedComputer):
        variant = None
        if lesson.event_type == EventType.PR1:
            practice_one = PracticeOne(computer_id, lesson, connected_computer.users_ids, db=self.db)
            if lesson.event_mode == EventMode.EXAM:
                variant = await practice_one.generate_exam()
            else:
                variant = await practice_one.generate_classic()
        elif lesson.event_type == EventType.PR2:
            ...
        elif lesson.event_type == EventType.CONTROL:
            ...
        return variant

    async def computers_exist(self):
        connected_computers = await self.state.get_connected_computers()
        if len(connected_computers) < 1:
            raise Exception('Нет подключенных компьютеров')

    async def type_and_mode_set(self):
        connected_computers = await self.state.get_connected_computers()
        for computer_id, connected_computer in connected_computers.items():
            if not all([connected_computer.event_mode, connected_computer.event_type]):
                raise Exception(f'Студенты сидящие за компьютером {computer_id} не выбрали работу')

    async def identical_mode(self):
        connected_computers = await self.state.get_connected_computers()
        mode = set()

        for connected_computer in connected_computers.values():
            mode.add(connected_computer.event_mode)

        if len(mode) > 1:
            raise Exception('Режим работы должен быть одинаков')

    async def remove_disconnected_computers(self):
        """Удаляем disconneted юзеров из connected_computers возможно они зашли случайно, а после перезашли с другого компьютера"""
        connected_computers = await self.state.get_connected_computers()
        for computer_id in list(connected_computers.keys()):
            if connected_computers[computer_id].is_connected is False:
                del connected_computers[computer_id]
        await self.state.set_connected_computers(connected_computers)
