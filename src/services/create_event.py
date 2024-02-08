from schemas import StartEventDto, EventType, EventMode
from services.practice_one import PracticeOne


def create_event(event_dto: StartEventDto, computer_id: int, users_ids: list[str]):
    if event_dto.type == EventType.PR1:
        if event_dto.mode == EventMode.CLASS:
            PracticeOne(computer_id=computer_id, users_ids=users_ids).create_pr1_class(event_dto)
