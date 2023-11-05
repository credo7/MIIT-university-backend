from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import models
from db.postgres import get_db
from services.service_collector import ServiceCollector
from services.event import EventService
from db.shared_state import shared_state

router = APIRouter(tags=['Events'], prefix='/events')


@router.get('/current-variant/{computer_id}')
async def get_current_variant(computer_id: int, db: Session = Depends(get_db)):
    event_service = EventService(db)
    event = await event_service.get_current_event_by_computer_id(computer_id, shared_state.lesson_id)
    variant = await event_service.get_variant_by_event(event)
    return variant


@router.post('/checkpoint')
def create_checkpoint(checkpoint_dto: schemas.CheckpointData, db: Session = Depends(get_db)):
    services = ServiceCollector(db)

    event: models.Event = services.event.get_current_event_by_computer_id(services, checkpoint_dto.computer_id)
    is_last_checkpoint = services.event.is_last_checkpoint(event)

    connected_computers = services.redis.get_connected_computers()
    users_ids = connected_computers[event.computer_id]
    users = services.user.get_users_by_ids(users_ids)
    services.event.create_checkpoints(event, checkpoint_dto, users=users)

    results = None
    if is_last_checkpoint:
        services.event.finish(event)
        results = services.event.get_results(event=event, users=users)

    current_step = services.event.get_current_step(event)
    services.redis.update_progress(event.computer_id, current_step)

    return {"next_step": services.event.get_current_step(event, just_check=True)} if not results else results


@router.get('/current-step/{computer_id}')
def get_current_step(computer_id: int, db: Session = Depends(get_db)):
    services = ServiceCollector(db)
    event: models.Event = services.event.get_current_event_by_computer_id(services, computer_id)
    current_step = services.event.get_current_step(event)

    results = None
    if current_step == "results":
        connected_computers = services.redis.get_connected_computers()
        users_ids = connected_computers[event.computer_id]
        users = services.user.get_users_by_ids(users_ids)
        results = services.event.get_results(event=event, users=users)

    return current_step if not results else results
