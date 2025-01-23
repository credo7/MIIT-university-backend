from typing import Optional, Type, Union

from db.mongo import get_db
from schemas import (
    CheckpointData,
    StartEventDto,
    PR2ControlEvent,
    PR2ControlStep2,
    PR2ControlStep1,
    PR2ControlStep3,
    CheckpointResponse,
)


class PracticeTwoControl:
    def __init__(self, users_ids: list[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    def create(self, event_dto: StartEventDto):
        PR2ControlEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            users_ids=self.users_ids,
            current_step='PR2_CONTROL_1',
            step1=PR2ControlStep1.create_variant(),
            step2=PR2ControlStep2.create_variant(),
            step3=PR2ControlStep3.create_variant(),
        )

    def checkpoint(self, event: Union[PR2ControlEvent, Type[PR2ControlEvent]], checkpoint_dto: CheckpointData):
        checkpoint_response = CheckpointResponse()

        if checkpoint_dto.step_code != event.current_step.code:
            raise Exception(f'Backend ждёт {event.current_step.code} step_code')

        if checkpoint_dto.step_code == 'PR2_CONTROL_1':
            ...

        if checkpoint_dto.step_code == 'PR2_CONTROL_2':
            ...

        if checkpoint_dto.step_code == 'PR2_CONTROL_3':
            ...

    def get_current_step(self, event: Union[PR2ControlEvent, Type[PR2ControlEvent]]):
        ...
