import json
from typing import List, Dict

import redis

from core.config import settings


class RedisService:
    def __init__(self):
        self.r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

    async def get_connected_computers(self) -> Dict[int, List[int]]:
        connected_computers = self.r.get("connected_computers")
        return connected_computers

    async def set_events_session_id(self, session_id):
        await self.r.set('events_session_id', session_id)
        return

    async def get_events_session_id(self):
        session_id = self.r.get('events_session_id')
        return session_id

    async def update_progress(self, computer_id: int, step):
        raw_progress = await self.r.get('progres')
        progress = json.loads(raw_progress)
        progress = [el for el in progress if el['computer_id'] != computer_id]
        dumped_progress = json.dumps({**progress, **{computer_id: step}})
        await self.r.set('progress', dumped_progress)
