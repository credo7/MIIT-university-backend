from typing import List, Dict

import schemas


class SocketHandlers:
    def connect(sid: str, environ: Dict):
        try:
            is_teacher, computer_id, user1, user2 = validate_tokens_or_raise(environ=environ, session=session, sid=sid)

            create_log_for_users(sio=sio, users=[user1, user2], endpoint='connection', computer_id=computer_id)

            if not is_teacher:
                update_connected_computers_and_session(
                    sid=sid,
                    session=session,
                    connected_computers=connected_computers,
                    user1=user1,
                    user2=user2,
                    computer_id=computer_id,
                )

            sio.emit('connected_computers', connected_computers)
        except Exception as e:
            sio.emit('errors', str(e))
            sio.disconnect(sid)

    @staticmethod
    def disconnect(sid: str):
        ...

    @staticmethod
    def start_events(sid: str, computers: List[schemas.StartEventComputer]):
        ...

    @staticmethod
    def start_late_events(sid: str, computers: List[schemas.StartEventComputer]):
        ...

    @staticmethod
    def raise_hand():
        ...

    @staticmethod
    def event_checkpoint():
        ...

    @staticmethod
    def logs():
        ...
