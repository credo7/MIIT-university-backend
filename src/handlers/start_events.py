import random
from typing import List

from bson import ObjectId

from pymongo.database import Database

from constants.practice_one_info import practice_one_info
from db.mongo import CollectionNames
from db.state import State
from schemas import Lesson, EventType, PracticeOneVariant, PracticeOneBet, EventInfo, EventStatus, ConnectedComputerEdit
from services.connection_manager import ConnectionManager
from services.utils import to_db


class StartEvents:
    def __init__(self, state: State, manager: ConnectionManager, db: Database):
        self.state = state
        self.manager = manager
        self.db = db

    async def run(self, *args, **kwargs):
        lesson = await self.state.get_lesson()
        if lesson is not None:
            # TODO: FINISH ALL OTHER EVENTS
            ...
        # TODO: Уточнить, а надо ли их удалять? Мб валидация
        await self.remove_disconnected_computers()
        await self.validate()

        lesson: Lesson = await self.create_and_set_lesson()
        await self.state.set_lesson(lesson)

        events = await self.generate_events(lesson)
        await to_db(events, CollectionNames.EVENTS.value)
        await self.manager.broadcast({"type": "STATUS", "payload": "START"})
        await self.set_started_status(events)

    async def set_started_status(self, events: List[EventInfo]):
        for event in events:
            edit_connected_computer = ConnectedComputerEdit(id=event.computer_id, status=EventStatus.STARTED.value)
            await self.state.edit_connected_computer(edit_connected_computer)

    async def validate(self):
        await self.computers_exist()
        await self.identical_type_mode()

    async def create_and_set_lesson(self) -> Lesson:
        connected_computers = await self.state.get_connected_computers()
        conn_computer = connected_computers[0]
        user = self.db[CollectionNames.USERS.value].find_one({
            "_id": ObjectId(conn_computer.users_ids[0])
        })
        group_id = user["group_id"]
        group_name = user["group_name"]
        event_type = conn_computer.event_type
        event_mode = conn_computer.event_mode

        lesson = Lesson(
            group_id=group_id,
            group_name=group_name,
            event_type=event_type,
            event_mode=event_mode
        )

        id = to_db(lesson.dict(), CollectionNames.LESSONS.value)

        lesson.id = id

        await self.state.set_lesson(lesson)

        return lesson

    @staticmethod
    async def generate_pr1_variant(computer_id: int, lesson: Lesson, users_ids: List[str]) -> PracticeOneVariant:
        # TODO: сделать функцию get_random_countries и больше стран
        random_points = ["ОТКУДА-ТО ТЕСТ", "КУДА-ТО ТЕСТ"]
        random.shuffle(random_points)
        product_options = ["КАКОЙ-ТО ТОВАР"]
        product = random.choice(product_options)
        from_country = random_points[0]
        to_country = random_points[1]
        product_price = random.randrange(1000, 9000, 100)
        legend = practice_one_info.legend_pattern.format(product, from_country, to_country, product_price)
        # TODO: STEP 2: Choose incoterms by first student
        random_incoterms = practice_one_info.all_incoterms.copy()
        random.shuffle(random_incoterms)
        random_incoterms = random_incoterms[:3]

        bets = []
        for bet_pattern in practice_one_info.bets:
            rate = random.randrange(bet_pattern.value.min, bet_pattern.value.max, bet_pattern.value.step)
            bet = PracticeOneBet(name=bet_pattern.name, rate=rate)
            bets.append(bet)

        return PracticeOneVariant(
            lesson_id=lesson.id,
            computer_id=computer_id,
            event_type=lesson.event_type,
            event_mode=lesson.event_mode,
            legend=legend,
            product=product,
            from_country=from_country,
            to_country=to_country,
            product_price=product_price,
            incoterms=random_incoterms,
            bets=bets,
            users_ids=users_ids
        )

    async def generate_events(self, lesson: Lesson):
        events = []

        connected_computers = await self.state.get_connected_computers()
        for computer_id, connected_computer in connected_computers.items():
            variant = None
            if lesson.event_type == EventType.PR1:
                variant = await self.generate_pr1_variant(computer_id, lesson, connected_computer.users_ids)
            elif lesson.event_type == EventType.PR2:
                ...
            elif lesson.event_type == EventType.CONTROL:
                ...
            events.append(variant)

        return events

    async def computers_exist(self):
        connected_computers = await self.state.get_connected_computers()
        if len(connected_computers) < 1:
            raise Exception("Нет подключенных компьютеров")

    async def identical_type_mode(self):
        """На одном уроке ученики могут выбрать только одинаковый тип работы и режим"""
        # TODO: А что с отработкой??
        connected_computers = await self.state.get_connected_computers()
        types = set()
        mode = set()

        for connected_computer in connected_computers.values():
            types.add(connected_computer.event_type)
            mode.add(connected_computer.event_mode)

        if len(types) > 1:
            raise Exception("Выбраны разные типы работ")

        if len(mode) > 1:
            raise Exception("Выбраны разные режимы работ")

    async def remove_disconnected_computers(self):
        """Удаляем disconneted юзеров из connected_computers возможно они зашли случайно, а после перезашли с другого компьютера"""
        connected_computers = await self.state.get_connected_computers()
        for computer_id, connected_computer in connected_computers.items():
            if connected_computer.is_connected is False:
                del connected_computers[computer_id]
        await self.state.set_connected_computers(connected_computers)
