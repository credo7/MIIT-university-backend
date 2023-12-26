from typing import Union, List
from bson import ObjectId

from pymongo.database import Database

from constants.practice_one_info import practice_one_info
from db.mongo import CollectionNames
from db.state import State
from schemas import EventType, PracticeOneVariant, EventInfo, StepRole, CheckpointData, EventStepResult, EventResult, \
    UserEventHistory, ConnectedComputerEdit, GeneralStep, Step, EventStatus
from services.utils import normalize_mongo


class EventService:
    def __init__(self, state: State, db: Database):
        self.state = state
        self.db: Database = db

    async def get_current_event_by_computer_id(self, computer_id: int) -> EventInfo:
        lesson = await self.state.get_lesson()
        event_db = self.db[CollectionNames.EVENTS.value].find_one({
            "lesson_id": lesson.id,
            "computer_id": computer_id
        })

        event = None
        if event_db["event_type"] == EventType.PR1.value:
            event = await normalize_mongo(event_db, PracticeOneVariant)

        return event

    @staticmethod
    async def get_current_step(event: EventInfo) -> Step:
        step = None
        if event.event_type == EventType.PR1.value:
            step = [step for step in practice_one_info.steps if step.index == event.step_index][0]

        return step

    async def finish_event(self, event: EventInfo, computer_id: int) -> List[EventResult]:
        event_results = []
        for user_id in event.users_ids:
            points = sum([step.points for step in event.steps_results if user_id in step.user_ids])
            fails = sum([step.fails for step in event.steps_results if user_id in step.user_ids])

            user = self.db[CollectionNames.USERS.value].find_one({"_id": ObjectId(user_id)})
            event_result = EventResult(fails=fails, points=points, **user)
            event_results.append(event_result)

            user["history"].append(UserEventHistory(**event_result.dict()).dict())

            self.db[CollectionNames.USERS.value].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "history": user["history"]
                    }
                }
            )

        self.db[CollectionNames.EVENTS.value].update_one(
            {"computer_id": event.computer_id, "lesson_id": event.lesson_id},
            {
                "is_finished": True,
                "results": [result.dict() for result in event_results],
            }
        )

        connected_computer_edit = ConnectedComputerEdit(id=computer_id, status=EventStatus.FINISHED.value)
        await self.state.edit_connected_computer(connected_computer_edit)

        return event_results

    async def create_checkpoint(self, event: EventInfo, checkpoint_dto: CheckpointData):
        if event.event_type == EventType.PR1.value:
            first_user_id = event.users_ids[0]
            second_user_id = event.users_ids[1] if len(event.users_ids) > 1 else None

            step = [step for step in practice_one_info.steps if step.index == event.step_index][0]

            candidates_user_ids = [first_user_id] if step.role in [StepRole.BUYER.value,
                                                                   StepRole.ALL.value] else []
            candidates_user_ids += [second_user_id] if second_user_id and step.role in [StepRole.SELLER.value,
                                                                                        StepRole.ALL.value] else []

            event_step_result = EventStepResult(
                step_index=step.index,
                user_ids=candidates_user_ids,
                points=checkpoint_dto.points,
                fails=checkpoint_dto.fails
            )

            event.steps_results.append(event_step_result)
            event_step_results = [result.dict() for result in event.steps_results]

            lesson = await self.state.get_lesson()
            updated_event = self.db[CollectionNames.EVENTS.value].find_one_and_update(
                {"lesson_id": lesson.id, "computer_id": checkpoint_dto.computer_id},
                {"$set": {"steps_results": event_step_results, "$inc": "step_index"}}
            )

            step_id = updated_event["step_index"]
            step_name = None
            if event.event_type == EventType.PR1.value:
                step_in_list = [step for step in practice_one_info.steps if step == step_id]
                if step_id > len(practice_one_info.steps):
                    step_name = "Работа завершена"
                else:
                    step_name = step_in_list[0].name

            general_step = GeneralStep(id=updated_event["step_index"], name=step_name)
            connected_computer_edit = ConnectedComputerEdit(id=checkpoint_dto.computer_id, step=general_step)

            await self.state.edit_connected_computer(connected_computer_edit)

    async def is_last_checkpoint(self, event: EventInfo):
        max_steps = None
        if event.event_type == 1:
            max_steps = len(practice_one_info.steps)

        if len(event.checkpoints) + 1 == max_steps:
            return True

        return False
