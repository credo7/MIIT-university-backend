from typing import Optional, List
import time

import models
from db.postgres import session as db_session


class ActionsLogger:
    def __init__(self, logs_to_db: bool = True, emit_logs: bool = True, errors_emit_logs: bool = True):
        self._logs_to_db = logs_to_db
        self._emit_logs = emit_logs
        self._errors_emit_logs = errors_emit_logs

    def log(
            self,
            sio,
            endpoint: str,
            computer_id: int,
            users_ids: Optional[List[int]] = None,
            users: Optional[List[models.User]] = None,
            logs_to_db: bool = True,
            emit_logs: bool = True
    ):
        if not users:
            if not users_ids:
                raise Exception("ActionLogger.create -> нет users_ids и users")
            else:
                for user_id in users_ids:
                    user = db_session.query(models.User).filter(models.User.id == user_id).first()
                    users.append(user)

        for user in users:
            if user is not None:
                log_from_db = None
                if logs_to_db and self._logs_to_db:
                    log_from_db = self._add_log_to_db(endpoint=endpoint, computer_id=computer_id, user=user)

                if emit_logs and self._emit_logs:
                    self._emit_log(sio=sio, endpoint=endpoint, log_from_db=log_from_db, computer_id=computer_id, user=user)

    @staticmethod
    def _add_log_to_db(endpoint: str, computer_id: int, user: models.User = None) -> models.Log:
        log = models.Log(user_id=user.id, endpoint=endpoint, computer_id=computer_id)
        db_session.add(log)
        db_session.commit()
        return log

    @staticmethod
    def _emit_log(sio, endpoint: str, log_from_db: Optional[models.Log], computer_id: int, user: models.User = None):
        sio.emit(
            'logs', f"{user.username} | {endpoint} | 'computer_id':{computer_id} | {log_from_db.created_at or time.time()}",
        )


