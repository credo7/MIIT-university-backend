from typing import Optional, Dict

import eventlet
import socketio

from core.config import settings
from schemas import CheckpointData
from services.socket_service import (
    create_event,
    create_events_session,
    create_log,
    create_log_for_users,
    create_users_checkpoints,
    emit_computer_event,
    finish_event,
    get_pr_type_by_event_id,
    update_connected_computers_and_session,
    validate_tokens_or_raise,
    raise_if_not_valid_teacher,
    raise_if_computers_already_started,
    get_last_step_number,
    raise_if_not_valid_start_events_input,
    raise_if_not_all_computers_connected,
    get_start_computers_status
)


class SocketServer:
    def __init__(self, logger: bool = False, cors_allowed_origins: Optional[str] = "*"):
        self.sio = socketio.Server(cors_allowed_origins=cors_allowed_origins, logger=logger)
        self.app = socketio.WSGIApp(self.sio, static_files={'/': {'content_type': 'text/html', 'filename': 'index.html'}})

        self.connected_computers = {}
        self.session = {}
        self.computers_status = {}
        self.session_id = {}

        self.sio.on('connect', self._connect)
        self.sio.on('disconnect', self._disconnect)
        self.sio.on('start_events', self._start_events)
        self.sio.on('start_late_events', self._start_late_events)
        self.sio.on('raise_hand', self._raise_hand)
        self.sio.on('event_checkpoint', self._event_checkpoint)
        self.sio.on('logs', self._logs)

    def run(self):
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), self.app)

    def _connect(self, sid: str, environ: Dict):
        try:
            is_teacher, computer_id, user1, user2 = validate_tokens_or_raise(environ=environ, session=self.session, sid=sid)

            create_log_for_users(sio=self.sio, users=[user1, user2], endpoint='connection', computer_id=computer_id)
            if not is_teacher:
                update_connected_computers_and_session(
                    sid=sid,
                    session=self.session,
                    connected_computers=self.connected_computers,
                    user1=user1,
                    user2=user2,
                    computer_id=computer_id,
                )

            self.sio.emit('connected_computers', self.connected_computers)
        except Exception as e:
            print(f"error is {e}")
            self.sio.emit('errors', str(e))
            self.sio.disconnect(sid)

    def _disconnect(self, sid):
        try:
            if sid not in self.session or 'ids' not in self.session[sid]:
                self.sio.emit('logs', 'Client without session was disconnected')
                return

            create_log_for_users(
                sio=self.sio, endpoint='disconnect', computer_id=self.session[sid]['computer_id'], users_ids=self.session[sid]['ids'],
            )

            if 'is_teacher' not in self.session[sid]:
                del connected_computers[self.session[sid]['computer_id']]

            self.sio.emit('connected_computers', connected_computers)
        except Exception as e:
            self.sio.emit('errors', str(e))
            self.sio.disconnect(sid)

    def _start_events(self, sid, computers):
        try:
            global computers_status, connected_computers, session_id
            raise_if_not_valid_start_events_input(computers)
            raise_if_not_all_computers_connected(computers, connected_computers)
            raise_if_not_valid_teacher(sid=sid, session=self.session, extra_text='start_events endpoint')

            events_session = create_events_session()

            # Запоминаем глобально айди текущей сессии (урока). Нужно в случае присоединения опоздавших
            session_id = events_session.id
            # Очищаем прошлый прогресс и добавляем начальный прогресс для новых connected учеников со step_id: 0, step_name: start
            computers_status = get_start_computers_status(computers, connected_computers)

            create_log(
                sio=self.sio, endpoint='create_event', computer_id=self.session[sid]['computer_id'], id=self.session[sid]['ids'][0],
            )

            for computer in computers:
                users = connected_computers[computer['id']]

                new_event = create_event(sio=self.sio, session_id=events_session.id, computer=computer, users=users)
                self.sio.emit(
                    'logs',
                    f'new_event_pr1 is {new_event.practice_one_variant}, new_event_pr2 is {new_event.practice_two_variant}',
                )
                emit_computer_event(
                    sio=self.sio,
                    computer=computer,
                    event_id=new_event.id,
                    variant=new_event.practice_one_variant if new_event.type == 1 else new_event.practice_two_variant,
                )
        except Exception as e:
            self.sio.emit('errors', str(e))
            self.sio.disconnect(sid)

    def _start_late_events(self, sid, computers):
        raise_if_not_valid_start_events_input(computers)
        raise_if_not_valid_teacher(sid=sid, session=self.session, extra_text='start_events endpoint')
        raise_if_computers_already_started(computers=computers, connected_computers=connected_computers)

    def _raise_hand(self, sid, _):
        try:
            if sid not in self.session or 'ids' not in self.session[sid]:
                self.sio.disconnect(sid)
                return

            requester_computer_id = self.session[sid]['computer_id']

            self.sio.emit("help_notification", {"computer_id": requester_computer_id})
        except Exception as e:
            self.sio.emit('errors', str(e))
            self.sio.disconnect(sid)

    def _event_checkpoint(self, sid, checkpoint_data: CheckpointData):
        try:
            if sid not in self.session or 'ids' not in self.session[sid]:
                self.sio.disconnect(sid)
                return

            create_users_checkpoints(
                sio=self.sio, sid=sid, session=self.session, checkpoint_data=checkpoint_data, computers_status=computers_status,
            )

            create_log_for_users(
                sio=self.sio,
                endpoint=f"checkpoint {checkpoint_data.step}",
                computer_id=self.session[sid]['computer_id'],
                users_ids=self.session[sid]['ids'],
            )

            event_type = get_pr_type_by_event_id(checkpoint_data.event_id)

            last_step_number = get_last_step_number(pr_type=event_type)

            if checkpoint_data.step == last_step_number:
                finish_event(sid=sid, sio=self.sio, session=self.session, event_id=checkpoint_data.event_id)

            self.sio.emit('events_status', computers_status)
        except Exception as e:
            self.sio.emit('errors', str(e))
            self.sio.disconnect(sid)

    def _logs(self, _sid, message):
        self.sio.emit("logs", message)
