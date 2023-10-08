from typing import Optional, List
import time
from bson import ObjectId
from datetime import datetime

from db.mongo import get_db, CollectionNames
import schemas


class ActionsLogger:
    def __init__(self, logs_to_db: bool = True, emit_logs: bool = True, errors_emit_logs: bool = True):
        self._logs_to_db = logs_to_db
        self._emit_logs = emit_logs
        self._errors_emit_logs = errors_emit_logs
        self._db = get_db()

    def log(
        self,
        sio,
        endpoint: str,
        computer_id: int,
        users_ids: Optional[List[str]] = None,
        users: Optional[List] = None,
        logs_to_db: bool = True,
        emit_logs: bool = True,
    ):
        if not users:
            users = []
            if not users_ids:
                raise Exception('ActionLogger.create -> нет users_ids и users')
            else:
                for user_id in users_ids:
                    user = self._db[CollectionNames.USERS.value].find_one({"_id": ObjectId(user_id)})
                    users.append(schemas.UserOut.mongo_to_json(user))

        for user in users:
            if user is not None:
                if logs_to_db and self._logs_to_db:
                    log = {
                        "user_id": str(user.get("_id")),
                        "created_at": datetime.now(),
                        "endpoint": endpoint,
                        "computer_id": computer_id
                    }
                    self._db[CollectionNames.LOGS.value].insert_one(log)

                if emit_logs and self._emit_logs:
                    sio.emit(
                        'logs',
                        f"{user.get('username') if user else ''} | {endpoint} | 'computer_id':{computer_id} | {time.time()}",
                    )
