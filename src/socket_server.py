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
    get_last_step_number
)

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={'/': {'content_type': 'text/html', 'filename': 'index.html'}})


connected_computers = {}
session = {}
computers_status = {}


@sio.on('connect')
def handle_connect(sid, environ):
    # try:
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
    # except Exception as e:
    #     sio.emit('errors', str(e))
    #     sio.disconnect(sid)


@sio.on('disconnect')
def handle_disconnect(sid):
    # try:
    if sid not in session or 'ids' not in session[sid]:
        sio.emit('logs', 'Client without session was disconnected')
        return

    create_log_for_users(
        sio=sio, endpoint='disconnect', computer_id=session[sid]['computer_id'], users_ids=session[sid]['ids'],
    )

    if not session[sid]['is_teacher']:
        del connected_computers[session[sid]['computer_id']]

    sio.emit('connected_computers', connected_computers)
    # except Exception as e:
    #     sio.emit('errors', str(e))
    #     sio.disconnect(sid)


@sio.on('start_events')
def start_events(sid, computers):
    # try:
    global computers_status, connected_computers
    raise_if_not_valid_teacher(sid=sid, session=session, extra_text='start_events endpoint')

    events_session = create_events_session()
    computers_status = {}

    create_log(
        sio=sio, endpoint='create_event', computer_id=session[sid]['computer_id'], id=session[sid]['ids'][0],
    )

    for computer in computers:
        users = connected_computers[int(computer['id'])]

        new_event = create_event(sio=sio, session_id=events_session.id, computer=computer, users=users)
        sio.emit(
            'logs',
            f'new_event_pr1 is {new_event.practice_one_variant}, new_event_pr2 is {new_event.practice_two_variant}',
        )
        emit_computer_event(
            sio=sio,
            computer=computer,
            event_id=new_event.id,
            variant=new_event.practice_one_variant if new_event.type == 1 else new_event.practice_two_variant,
        )


# except Exception as e:
#     sio.emit('errors', str(e))
#     sio.disconnect(sid)


@sio.on('event_checkpoint')
def checkpoint(sid, checkpoint_data: CheckpointData):
    try:
        if sid not in session or 'ids' not in session[sid]:
            sio.disconnect(sid)
            return

        create_users_checkpoints(
            sio=sio, sid=sid, session=session, checkpoint_data=checkpoint_data, computers_status=computers_status,
        )

        create_log_for_users(
            sio=sio,
            endpoint=f"checkpoint {checkpoint_data['step']}",
            computer_id=session[sid]['computer_id'],
            users_ids=session[sid]['ids'],
        )

        event_type = get_pr_type_by_event_id(checkpoint_data['event_id'])

        last_step_number = get_last_step_number(pr_type=event_type)

        if checkpoint_data['step'] == last_step_number:
            finish_event(sid=sid, sio=sio, session=session, event_id=checkpoint_data['event_id'])

        sio.emit('events_status', computers_status)
    except Exception as e:
        sio.emit('errors', str(e))
        sio.disconnect(sid)


@sio.on('logs')
def logs(sid, message):
    sio.emit("logs", message)


def start_socket_server():
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), app)
