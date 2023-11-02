from sqlalchemy.orm import Session as DBSession

from services.event import EventService
from services.redis2 import RedisService
from services.user import UserService


class ServiceCollector:
    def __init__(self, db_session: DBSession):
        self._db_session = db_session

        self.event: EventService = EventService(self._db_session)
        self.user: UserService = UserService(self._db_session)
        self.redis: RedisService = RedisService()