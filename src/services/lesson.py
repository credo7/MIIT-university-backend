from pymongo.database import Database

from db.mongo import CollectionNames
from db.state import State
from schemas import EventInfo, EventResult
from services.utils import normalize_mongo


class LessonService:
    def __init__(self, db: Database):
        self.db: Database = db

    def get_current_lesson_results(self) -> dict[int, list[EventResult]]:
        events_db = self.db[CollectionNames.EVENTS.value].find({'lesson_id': State.lesson.id})

        events: list[EventInfo] = normalize_mongo(events_db, EventInfo)

        event_results = {event.computer_id: event.results for event in events}

        return event_results
