from typing import Dict, List

from sqlalchemy.orm import Session

import models
from schemas import ConnectedComputer


class DataService:
    def __init__(self, db_session: Session):
        self._db_session = db_session

    async def create_lesson(self) -> models.Lesson:
        lesson = models.Lesson()
        self._db_session.add(lesson)
        self._db_session.commit()
        return lesson

    async def insert_events(self, events: List[models.Event]):
        self._db_session.bulk_save_objects(events)
        self._db_session.commit()
