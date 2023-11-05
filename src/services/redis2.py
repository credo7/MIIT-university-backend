import json
from typing import List, Dict

import redis

from core.config import settings
from schemas import UserOut


class RedisService:
    def __init__(self):
        self._r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
        self._events_session_id = None

    def upsert_connected_computers(self, connected_computers: Dict[int, List[int]]):
        s = json.dumps(connected_computers)
        self._r.set("connected_computers", s)

    def get_connected_computers(self) -> Dict[int, List[int]]:
        s = self._r.get("connected_computers")
        connected_computers = json.loads(s)
        return connected_computers

    def set_events_session_id(self, session_id):
        self._r.set('events_session_id', session_id)

    def get_events_session_id(self):
        session_id = self._r.get('events_session_id')
        return session_id

    def update_progress(self, computer_id: int, step):
        raw_progress = self._r.get('progres')
        progress = []
        if raw_progress:
            progress = json.loads(raw_progress)
        progress = [el for el in progress if el['computer_id'] != computer_id]
        dumped_progress = json.dumps([*progress, {computer_id: step}])
        self._r.set('progress', dumped_progress)
