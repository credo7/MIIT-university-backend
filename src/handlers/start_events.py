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
    def __init__(self, db: Database):
        self.db = db
        self.event_service = EventService(db=self.db)

    async def run(self, is_teacher, *_args, **_kwargs):
        if not is_teacher:
            raise Exception('Только учитель может запускать работу. Чекается по токену первого юзера')
        if State.lesson is not None:
            await self.event_service.finish_current_lesson()
        self.remove_disconnected_computers()
        self.validate()

        lesson: Lesson = self.create_and_set_lesson()

        events = self.generate_events(lesson)
        to_db(events, CollectionNames.EVENTS.value)
        await State.manager.broadcast({'type': 'STATUS', 'payload': 'START'})
        self.set_started_status(events)

    @staticmethod
    def set_started_status(events: List[EventInfo]):
        for event in events:
            edit_connected_computer = ConnectedComputerEdit(id=event.computer_id, status=EventStatus.STARTED.value)
            State.edit_connected_computer(edit_connected_computer)

    def validate(self):
        self.computers_exist()
        self.type_and_mode_set()
        self.identical_mode()

    def create_and_set_lesson(self) -> Lesson:
        conn_computer = list(State.connected_computers.values())[0]
        user = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(conn_computer.users_ids[0])})
        group_id = user['group_id']
        group_name = user['group_name']
        event_type = conn_computer.event_type
        event_mode = conn_computer.event_mode

        lesson = Lesson(group_id=group_id, group_name=group_name, event_type=event_type, event_mode=event_mode,)

        id = to_db(lesson.dict(), CollectionNames.LESSONS.value)

        lesson.id = id

        State.lesson = lesson

        return lesson

    def generate_events(self, lesson: Lesson):
        events = []

        for computer_id, connected_computer in State.connected_computers.items():
            variant = self.get_variant(lesson, computer_id, connected_computer)
            events.append(variant)

        return events

    def get_variant(self, lesson: Lesson, computer_id: int, connected_computer: ConnectedComputer):
        variant = None
        if lesson.event_type == EventType.PR1:
            practice_one = PracticeOne(computer_id, lesson, connected_computer.users_ids, db=self.db)
            if lesson.event_mode == EventMode.EXAM:
                variant = practice_one.generate_exam()
            else:
                variant = practice_one.generate_classic()
                _ = 1
        elif lesson.event_type == EventType.PR2:
            ...
        elif lesson.event_type == EventType.CONTROL:
            ...
        return variant

    def computers_exist(self):
        if len(State.connected_computers) < 1:
            raise Exception('Нет подключенных компьютеров')

    def type_and_mode_set(self):
        for computer_id, connected_computer in State.connected_computers.items():
            if not all([connected_computer.event_mode, connected_computer.event_type]):
                raise Exception(f'Студенты сидящие за компьютером {computer_id} не выбрали работу')

    def identical_mode(self):
        mode = set()

        for connected_computer in State.connected_computers.values():
            mode.add(connected_computer.event_mode)

        if len(mode) > 1:
            raise Exception('Режим работы должен быть одинаков')

    def remove_disconnected_computers(self):
        """Удаляем disconneted юзеров из connected_computers возможно они зашли случайно, а после перезашли с другого компьютера"""
        for computer_id in list(State.connected_computers.keys()):
            if State.connected_computers[computer_id].is_connected is False:
                del State.connected_computers[computer_id]
