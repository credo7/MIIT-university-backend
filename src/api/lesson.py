import logging

from fastapi import APIRouter, Depends
from pymongo.database import Database

from db.mongo import get_db, CollectionNames
from schemas import EventResult
from services.lesson import LessonService

router = APIRouter(tags=['Lessons'], prefix='/lessons')

logger = logging.getLogger(__name__)

lesson_service = LessonService(db=get_db())


@router.get('/current-results', response_model=dict[int, list[EventResult]])
async def get_current_lesson_results(
        db: Database = Depends(get_db),

):
    event_db = db[CollectionNames.EVENTS.value].find_one()
