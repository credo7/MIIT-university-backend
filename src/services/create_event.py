from typing import Union, Type

from schemas import StartEventDto, EventType, EventMode, PR1ClassEvent, EventInfo
from services.practice_one_class import PracticeOneClass
from services.practice_one_control import PracticeOneControl


def create_event(event_dto: StartEventDto, users_ids: list[str]) -> Type[EventInfo]:
    if event_dto.type == EventType.PR1:
        if event_dto.mode == EventMode.CLASS:
            return PracticeOneClass(computer_id=event_dto.computer_id, users_ids=users_ids).create(event_dto)
        elif event_dto.mode == EventMode.CONTROL:
            return PracticeOneControl(computer_id=event_dto.computer_id, users_ids=users_ids).create(event_dto)
