import logging

from fastapi import APIRouter

from db.mongo import get_db
from schemas import EventResult
from services.lesson import LessonService

router = APIRouter(tags=['Lessons'], prefix='/lessons')

logger = logging.getLogger(__name__)

lesson_service = LessonService(db=get_db())


@router.get('/current-results', response_model=dict[int, list[EventResult]])
async def get_current_lesson_results():
    results = lesson_service.get_current_lesson_results()
    return results