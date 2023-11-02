from typing import List

from sqlalchemy.orm import Session as DBSession

import models


class UserService:
    def __init__(self, db_session: DBSession):
        self._db_session = db_session

    def get_users_by_ids(self, ids: List):
        users = self._db_session.query(models.User).filter(models.User.id.in_(ids)).all()
        return users
