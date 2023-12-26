from typing import Union

from fastapi import APIRouter

import schemas
from schemas import PracticeOneVariant
from db.mongo import get_db
from services.event import EventService
from db.state import state

router = APIRouter(tags=['Events'], prefix='/events')

event_service = EventService(state, db=get_db())


@router.get('/current-variant/{computer_id}', response_model=Union[PracticeOneVariant])
async def get_current_variant(computer_id: int):
    variant = await event_service.get_current_event_by_computer_id(computer_id)
    return variant


@router.post('/checkpoint')
async def create_checkpoint(checkpoint_dto: schemas.CheckpointData):
    event = await event_service.get_current_event_by_computer_id(checkpoint_dto.computer_id)
    is_last_checkpoint = await event_service.is_last_checkpoint(event)

    await event_service.create_checkpoint(event, checkpoint_dto)

    results = None
    if is_last_checkpoint:
        results = await event_service.finish_event(event, checkpoint_dto.computer_id)

    next_step = None
    if not results:
        next_step = await event_service.get_current_step(event)

    return {"next_step": next_step.dict()} if not results else results


@router.get('/current-step/{computer_id}')
async def get_current_step(computer_id: int):
    event = await event_service.get_current_event_by_computer_id(computer_id)

    if event.is_finished:
        return event.results

    current_step = await event_service.get_current_step(event)

    return current_step
