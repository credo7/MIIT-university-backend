import random
from typing import List

from bson import ObjectId

from pymongo.database import Database

from db.mongo import CollectionNames
from db.state import State
from schemas import (
    Lesson,
    EventInfo,
    EventStatus,
    ConnectedComputerEdit,
)
from services.event import EventService
from services.utils import to_db


class StartEvents:
    def __init__(self, db: Database):
        self.db = db
        self.event_service = EventService(db=self.db)

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
