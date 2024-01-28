from typing import Union, List, Optional

import pymongo
from bson import ObjectId

from pymongo.database import Database

from constants.practice_one_info import practice_one_info
from db.mongo import CollectionNames
from db.state import State
from schemas import (
    EventType,
    PracticeOneVariant,
    EventInfo,
    StepRole,
    CheckpointData,
    EventStepResult,
    EventResult,
    UserEventHistory,
    ConnectedComputerEdit,
    GeneralStep,
    Step,
    EventStatus,
    EventMode,
    UserOut,
)
from services.utils import normalize_mongo


class EventService:
    def __init__(self, db: Database):
        self.db: Database = db

    def get_current_event_by_user_id(self, user: UserOut) -> EventInfo:
        for computer_id, connected_computer in State.connected_computers.items():
            if user.id in connected_computer.users_ids:
                return self.get_current_event_by_computer_id(connected_computer.id)
        raise Exception('Юзер не подключен к какому-либо компьютеру')

    def get_current_event_by_computer_id(self, computer_id: int) -> EventInfo:
        event_db = self.db[CollectionNames.EVENTS.value].find_one({'lesson_id': State.lesson.id, 'computer_id': computer_id})

        if not event_db:
            raise Exception('Вариант не найден')

        event = None
        if event_db['event_type'] == EventType.PR1.value:
            event = normalize_mongo(event_db, PracticeOneVariant)

        return event

    @staticmethod
    def get_current_step(event: EventInfo) -> Step:
        step = None
        if event.event_type == EventType.PR1.value:
            step = [step for step in practice_one_info.steps if step.index == event.step_index][0]

        return step

    def finish_event(self, event: EventInfo, by_teacher: Optional = False) -> List[EventResult]:
        """
            by_teacher: bool -> Завершение учителем
            Если работу завершает учитель - значит ученик не успел ее завершить сам и работа считается заваленной.
            Даже если ему не хватило лишь последнего задания.
        """
        event_results = []
        for user_id in event.users_ids:
            user = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user_id)})

            points = sum([step.points for step in event.steps_results if user_id in step.user_ids])
            fails = sum([step.fails for step in event.steps_results if user_id in step.user_ids])
            event_result = EventResult(fails=fails, points=points, **user)
            event_results.append(event_result)

            user_event_result = UserEventHistory(
                lesson_id=event.lesson_id,
                event_id=event.id,
                event_type=event.event_type,
                event_mode=event.event_mode,
                points=0 if by_teacher else points,
                fails=0 if by_teacher else event_result.fails,
                is_failed=True if by_teacher else False,
            )

            self.db[CollectionNames.USERS.value].update_one(
                {'_id': ObjectId(user_id)}, {'$push': {'history': user_event_result.dict()}}
            )

        self.db[CollectionNames.EVENTS.value].update_one(
            {'computer_id': event.computer_id, 'lesson_id': event.lesson_id},
            {
                '$set': {'is_finished': True, 'is_failed': True if by_teacher else False},
                '$push': {'results': {'$each': [el.dict() for el in event_results]}},
            },
        )

        if event.event_type == EventType.PR1 and event.event_mode != EventMode.EXAM and not by_teacher:
            self.update_users_incoterms(event)

        connected_computer_edit = ConnectedComputerEdit(id=event.computer_id, status=EventStatus.FINISHED.value)
        State.edit_connected_computer(connected_computer_edit)

        return event_results

    def update_users_incoterms(self, event: EventInfo):
        """
            Обновляем рузультаты пользователя по инкотермам
            Сначала по базовым заданиям ( таблицы )
            После по тестовым вопросам
            Зависят от индексов степов, если они поменяются, то тут тоже нужно менять!
        """
        pr1_event_db = self.db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event.id)})
        pr1_variant: PracticeOneVariant = normalize_mongo(pr1_event_db, PracticeOneVariant)

        first_incoterm_steps_id = (1, 2)
        second_incoterm_steps_id = (3, 4)
        _third_incoterm_steps_id = (5, 6)

        for user_id in event.users_ids:
            update_incoterms = {}
            for step_result in pr1_variant.steps_results:
                if 1 <= step_result.step_index <= 6:
                    if user_id in step_result.user_ids:
                        if step_result.step_index in first_incoterm_steps_id:
                            incoterm = pr1_variant.incoterms[0]
                        elif step_result.step_index in second_incoterm_steps_id:
                            incoterm = pr1_variant.incoterms[1]
                        else:
                            incoterm = pr1_variant.incoterms[2]
                        update_incoterms[incoterm] = update_incoterms.get(incoterm, 0) + step_result.points

            user_db = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user_id)})
            user_incoterms = user_db.get('incoterms', None)
            if not user_incoterms:
                user_incoterms = update_incoterms
            else:
                for incoterm, points in update_incoterms.items():
                    user_incoterms[incoterm] = user_incoterms.get(incoterm, 0) + points
            self.db[CollectionNames.USERS.value].update_one(
                {'_id': ObjectId(user_id)}, {'$set': {'incoterms': user_incoterms}}
            )

    async def finish_current_lesson(self, *_args, **_kwargs):
        events_db = self.db[CollectionNames.EVENTS.value].find({'lesson_id': State.lesson.id})

        for event_db in events_db:
            if event_db['is_finished'] is False:
                event = normalize_mongo(event_db, EventInfo)
                self.finish_event(event=event, by_teacher=True)

    def create_checkpoint(self, event: EventInfo, checkpoint_dto: CheckpointData, is_last: bool):
        if event.event_type == EventType.PR1.value:
            if event.event_mode != EventMode.EXAM:
                first_user_id = event.users_ids[0]
                second_user_id = event.users_ids[1] if len(event.users_ids) > 1 else None
                step = [step for step in practice_one_info.steps if step.index == event.step_index][0]

                candidates_user_ids = [first_user_id] if step.role in [StepRole.BUYER.value, StepRole.ALL.value] else []
                candidates_user_ids += (
                    [second_user_id]
                    if second_user_id and step.role in [StepRole.SELLER.value, StepRole.ALL.value]
                    else []
                )

                event_step_result = EventStepResult(
                    step_index=step.index,
                    user_ids=candidates_user_ids,
                    points=checkpoint_dto.points,
                    fails=checkpoint_dto.fails,
                )

                if checkpoint_dto.description:
                    event_step_result.description = checkpoint_dto.description

                event.steps_results.append(event_step_result)
                event_step_results = [result.dict() for result in event.steps_results]

                updated_event = self.db[CollectionNames.EVENTS.value].find_one_and_update(
                    {'lesson_id': State.lesson.id, 'computer_id': event.computer_id},
                    {'$set': {'steps_results': event_step_results}, '$inc': {'step_index': 1}},
                    return_document=pymongo.ReturnDocument.AFTER,
                )

                step_id = updated_event['step_index']
                step_name = None
                if event.event_type == EventType.PR1.value:
                    step_in_list = [step for step in practice_one_info.steps if step.index == step_id]
                    if is_last:
                        step_name = 'Работа завершена'
                    else:
                        step_name = step_in_list[0].name

                general_step = GeneralStep(id=updated_event['step_index'], name=step_name)
                connected_computer_edit = ConnectedComputerEdit(id=event.computer_id, step=general_step)

                State.edit_connected_computer(connected_computer_edit)

    @staticmethod
    def is_last_checkpoint(event: EventInfo):
        max_steps = None
        if event.event_type == EventType.PR1:
            max_steps = len(practice_one_info.steps)

        if event.step_index == max_steps:
            return True

        return False
