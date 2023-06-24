import eventlet
import socketio

import database
from schemas import CheckpointData
from config import settings
from socker_service import emit_connected_computers, update_session, validate_tokens, is_valid_teacher_session, \
    create_events_session, create_event, get_random_practice_one_variant, emit_computer_event, finish_event, \
    create_users_checkpoints



sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

connected_computers = {}
session = {}
computers_status = {}


@sio.on('connect')
def handle_connect(sid, environ):
    tokens_valid, user, computer_id, user2, is_teacher = validate_tokens(environ, session, sid)

    if not all([tokens_valid, user, computer_id]):
        sio.disconnect(sid)
        return
    
    if not is_teacher:
        update_session(sid=sid, session=session, connected_computers=connected_computers, user=user,
                        user2=user2, computer_id=computer_id)
    
    emit_connected_computers(sio=sio, connected_computers=connected_computers)



@sio.on('disconnect')
def handle_disconnect(sid):
    if not sid in session or "ids" not in session[sid]:
        print("Client without session was disconnected", flush=True)
        return

    del connected_computers[session[sid]["computer_id"]]

    emit_connected_computers(sio=sio, connected_computers=connected_computers)


@sio.on('start_events')
def start_events(sid, computers):
    global computers_status, connected_computers
    if not is_valid_teacher_session(sid=sid, session=session):
        sio.disconnect(sid)
        return
    
    events_session = create_events_session()
    computers_status = {}

    for computer in computers:
        sio.emit('logs', computer)
        users = connected_computers[int(computer["id"])]

        random_variant = None
        if computer["type"] == 1:
            random_variant = get_random_practice_one_variant()

        new_event = create_event(session_id=events_session.id, computer=computer, users=users, variant=random_variant)
        emit_computer_event(sio=sio, computer=computer, event_id=new_event.id, variant=random_variant)


@sio.on('event_checkpoint')
def checkpoint(sid, checkpoint_data: CheckpointData):
    if sid not in session or "ids" not in session[sid]:
        sio.disconnect(sid)
        return
    
    create_users_checkpoints(sio=sio, sid=sid, session=session, checkpoint_data=checkpoint_data, computers_status=computers_status)

    if checkpoint_data["step"] == settings.pr1_last_step_number:
        finish_event(sid=sid, sio=sio, session=session, event_id=checkpoint_data["event_id"])
        
    sio.emit('events_status', computers_status)
    

def start_socket_server():
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), app)
