from typing import Union
import logging

from fastapi import APIRouter, Depends

from schemas import PracticeOneVariant, StartEventDto, UserOut, CheckpointData
from db.mongo import get_db
from services import oauth2
from services.create_event import create_event
from services.event import EventService
from services.ws import broadcast_connected_computers

router = APIRouter(tags=['Events'], prefix='/events')

event_service = EventService(db=get_db())

logger = logging.getLogger(__name__)


@router.post('/start')
async def start_event(start_event_dto: StartEventDto):
    create_event(start_event_dto)
    return {"message": "success"}


@router.get('/current-variant/{computer_id}', response_model=Union[PracticeOneVariant])
async def get_current_variant(computer_id: int):
    variant = event_service.get_current_event_by_computer_id(computer_id)
    logger.info(f'variant with id {variant.id}')
    return variant


@router.post('/checkpoint')
async def create_checkpoint(
    checkpoint_dto: CheckpointData, current_user: UserOut = Depends(oauth2.get_current_user),
):
    event = event_service.get_current_event_by_user_id(current_user)
    if event.is_finished:
        return {'results': event.results}

    is_last_checkpoint = event_service.is_last_checkpoint(event)

    event_service.create_checkpoint(event, checkpoint_dto, is_last_checkpoint)

    results = None
    if is_last_checkpoint:
        results = event_service.finish_event(event)

    next_step = None
    if not results:
        # Косяк. Делаем так, потому что внутри предыдущих функций используем другой инстанс евента
        event.step_index += 1
        next_step = event_service.get_current_step(event)

    await broadcast_connected_computers()

    return {'next_step': next_step.dict()} if not results else {'results': results}


@router.get('/current-step/{computer_id}')
async def get_current_step(computer_id: int):
    event = event_service.get_current_event_by_computer_id(computer_id)

    if event.is_finished:
        return event.results

    current_step = event_service.get_current_step(event)

    logger.info(f'current_step = {current_step}')

    return current_step