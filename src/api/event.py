from typing import List

from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

import schemas
import models
from models import User
from db.postgres import get_db
from services import oauth2
from services.service_collector import ServiceCollector

router = APIRouter(tags=['Events'], prefix='/events')


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=None)
async def create(
        events: List[schemas.StartEventComputer],
        current_user: User = Depends(oauth2.get_current_user),
        db: Session = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    # TODO Check if all computers are connected

    services = ServiceCollector(db)

    events_session = services.event.create_events_session()
    connected_computers = await services.redis.get_connected_computers()
    await services.redis.set_events_session_id(events_session.id)

    for event in events:
        users_ids = connected_computers[event.computer_id]
        users = services.user.get_users_by_ids(users_ids)
        services.event.create_event(event=event, users=users, events_session=events_session)


@router.get('/current-variant/{computer_id}')
async def get_current_event(computer_id: int, db: Session = Depends(get_db)):
    services = ServiceCollector(db)
    event: models.Event = await services.event.get_current_event_by_computer_id(services, computer_id)
    variant = await services.event.get_variant_by_event(event)
    return variant


@router.post('/checkpoint')
async def create_checkpoint(checkpoint_dto: schemas.CheckpointData, db: Session = Depends(get_db)):
    services = ServiceCollector(db)

    event: models.Event = await services.event.get_current_event_by_computer_id(services, checkpoint_dto.computer_id)
    is_last_checkpoint = services.event.is_last_checkpoint(event)

    connected_computers = await services.redis.get_connected_computers()
    users_ids = connected_computers[event.computer_id]
    users = services.user.get_users_by_ids(users_ids)
    await services.event.create_checkpoints(event, checkpoint_dto, users=users)

    results = None
    if is_last_checkpoint:
        await services.event.finish(event)
        results = await services.event.get_results(event=event, users=users)

    current_step = await services.event.get_current_step(event)
    await services.redis.update_progress(event.computer_id, current_step)

    return {"message": "OK!"} if not results else results


@router.get('/current-step/{computer_id}')
async def get_current_step(computer_id: int, db: Session = Depends(get_db)):
    services = ServiceCollector(db)
    event: models.Event = await services.event.get_current_event_by_computer_id(services, computer_id)
    current_step = await services.event.get_current_step(event)

    results = None
    if current_step == "results":
        connected_computers = await services.redis.get_connected_computers()
        users_ids = connected_computers[event.computer_id]
        users = services.user.get_users_by_ids(users_ids)
        results = await services.event.get_results(event=event, users=users)

    return current_step if not results else results
