from pymongo.database import Database

from db.mongo import CollectionNames
from db.state import State
from schemas import EventInfo, EventResult
from services.utils import normalize_mongo


class LessonService:
    def __init__(self, state: State, db: Database):
        self.state = state
        self.db: Database = db

    async def get_current_lesson_results(self) -> dict[int, list[EventResult]]:
        lesson = await self.state.get_lesson()
        events_db = self.db[CollectionNames.EVENTS.value].find({'lesson_id': lesson.id})

        events: list[EventInfo] = await normalize_mongo(events_db, EventInfo)

        event_results = {event.computer_id: event.results for event in events}

        return event_results
