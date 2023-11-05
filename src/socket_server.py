from typing import Optional, Dict, Tuple, List

import socketio
from sqlalchemy.orm import Session as DBSession

import models
from schemas import UserOut
from services import oauth2
from services.actions_logger import ActionsLogger
from services.redis2 import RedisService


class SocketServer:
    def __init__(self, db_session: DBSession, logger: bool = False, cors_allowed_origins: Optional[str] = '*'):
        self._sio = socketio.AsyncServer(cors_allowed_origins=cors_allowed_origins, logger=logger, async_mode='asgi')
        self.app = socketio.ASGIApp(
            self._sio, static_files={'/': {'content_type': 'text/html', 'filename': 'index.html'}}
        )
        self._logger = ActionsLogger()
        self._redis = RedisService()
        self._db_session = db_session

        self._connected_computers = {}
        self._session = {}
        self._computers_status = {}
        self._events_session = None

        self._sio.on('connect', self._connect)
        self._sio.on('disconnect', self._disconnect)
        self._sio.on('start', self._start)

    def _start(self):
        self._sio.emit("start")

    def _finish(self):
        self._sio.emit("finish")

    async def _connect(self, sid: str, environ: Dict, *args, **kwargs):
        try:
            if environ.get('HTTP_COMMANDER'):
                return

            is_teacher, computer_id, users = self.__validate_tokens_or_raise(environ=environ, sid=sid)

            # self._logger.log(sio=self._sio, users=users, endpoint='connection', computer_id=computer_id)

            if not is_teacher:
                self.__update_connected_computers_and_session(
                    sid=sid, users=users, computer_id=computer_id,
                )

            self._redis.upsert_connected_computers(await self._connected_computers_ids_mapping())

            await self._sio.emit('connected_computers', self._connected_computers)
        except Exception as e:
            await self._sio.emit('errors', str(e))
            await self._sio.disconnect(sid)

    async def _connected_computers_ids_mapping(self):
        # TODO: Сделать одинаковый формат везде
        connected_computers_ids_mapping = {}
        for computer_id, users in self._connected_computers:
            users_ids = []
            for user in users:
                users_ids.append(user["id"])
            connected_computers_ids_mapping[computer_id] = users_ids
        return connected_computers_ids_mapping

    async def _disconnect(self, sid):
        try:
            if sid not in self._session or 'ids' not in self._session[sid]:
                await self._sio.emit('logs', 'Client without session was disconnected')
                return

            # self._logger.log(
            #     sio=self._sio,
            #     endpoint='disconnect',
            #     computer_id=self._session[sid]['computer_id'],
            #     users_ids=self._session[sid]['ids'],
            # )

            if 'is_teacher' not in self._session[sid]:
                del self._connected_computers[self._session[sid]['computer_id']]
                self._redis.upsert_connected_computers(await self._connected_computers_ids_mapping())

            await self._sio.emit('connected_computers', self._connected_computers)
        except Exception as e:
            await self._sio.emit('errors', str(e))
            await self._sio.disconnect(sid)

    def __validate_tokens_or_raise(
        self, sid, environ
    ) -> Tuple[bool, Optional[int], List[models.User]]:
        """Function checks if computer id is set, if user is Teacher, if tokens are valid or raise an Exception."""
        first_token = environ.get('HTTP_AUTHORIZATION')
        second_token = environ.get('HTTP_AUTHORIZATION_TWO')

        if not first_token or first_token == second_token:
            raise Exception("First token wasn't provided or tokens are the same")

        user = oauth2.get_current_user_socket(first_token)
        if not user:
            raise Exception("User wasn't found")

        if not user.approved:
            raise Exception("User wasn't approved")

        computer_id = environ.get('HTTP_COMPUTER_ID')
        if not computer_id:
            raise Exception("Computer id wasn't provided")

        computer_id = int(computer_id)
        self._session.setdefault(sid, {})

        if user.role == 'TEACHER':
            self._session[sid]['is_teacher'] = True
            self._session[sid]['ids'] = [user.id]
            self._session[sid]['computer_id'] = computer_id
            return True, computer_id, [user]

        if second_token:
            user2 = oauth2.get_current_user_socket(second_token)
            if not user2:
                raise Exception('Second authorization token is not correct')
            if not user2.approved:
                raise Exception("Second user wasn't approved")
            return False, computer_id, [user, user2]

        return False, computer_id, [user]

    def __update_connected_computers_and_session(self, sid, users: List[models.User], computer_id: int):
        self._connected_computers[computer_id] = [users[0].serialize()]
        user_ids = [users[0].id]
        user_usernames = [users[0].username]

        if len(users) > 1:
            self._connected_computers[computer_id].append(users[1].serialize())
            user_ids.append(users[1].id)
            user_usernames.append(users[1].username)

        self._session[sid]['ids'] = user_ids
        self._session[sid]['usernames'] = user_usernames
        self._session[sid]['computer_id'] = computer_id
