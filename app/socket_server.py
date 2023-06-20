import eventlet
from sqlalchemy.sql.expression import func
import socketio

from config import settings
import database
import models
import oauth2


sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

connected_computers, session, computers_status = {}, {}, {}

LAST_STEP_NUMBER = 15


@sio.on('connect')
def handle_connect(sid, environ):
    first_token = environ.get('HTTP_AUTHORIZATION')
    second_token = environ.get('HTTP_AUTHORIZATION_TWO')

    if not first_token or first_token == second_token:
        print("First token wasn't provided or tokens are the same", flush=True)
        sio.disconnect(sid)
        return

    user = oauth2.get_current_user_socket(first_token)

    if not user:
        print("User wasn't found", flush=True)
        sio.disconnect(sid)
        return

    session.setdefault(sid, {})

    if user.role == "TEACHER":
        session[sid]["is_teacher"] = True
        return

    computer_id = environ.get("HTTP_COMPUTER_ID")

    if not computer_id:
        print("Computer id wasn't provided", flush=True)
        sio.disconnect(sid)
        return

    user2 = None
    if second_token:
        user2 = oauth2.get_current_user_socket(second_token)
        if not user2:
            print("Second authorization token is not correct", flush=True)
            sio.disconnect(sid)
            return

    connected_computers[computer_id] = [user.serialize()]

    user_ids = [user.id]
    user_usernames = [user.username]

    if user2:
        connected_computers[computer_id].append(user.serialize())
        user_ids.append(user2.id)
        user_usernames.append(user2.username)

    session[sid]["ids"] = user_ids
    session[sid]["usernames"] = user_usernames
    session[sid]["computer_id"] = computer_id

    message = f'User {user.username} with ID {user.id} connected to socket with computer id {computer_id}'
    if user2:
        message += f' and {user2.username} with ID {user2.id}'
    else:
        message += ' without a second user'
    print(message, flush=True)
    sio.emit('connected_computers', connected_computers)



@sio.on('disconnect')
def handle_disconnect(sid):
    if not sid in session or "ids" not in session[sid]:
        print("Client without session was disconnected", flush=True)
        return

    del connected_computers[session[sid]["computer_id"]]

    message = f'User {session[sid]["usernames"][0]} with ID {session[sid]["ids"][0]} connected to socket'
    if "ids" in session[sid] and len(session[sid]["ids"]) > 1:
        message += f' and {session[sid]["usernames"][1]} with ID {session[sid]["ids"][1]}'
    else:
        message += ' without a second user'

    print(message, flush=True)

    sio.emit('connected_computers', connected_computers)


@sio.on('start_events')
def start_events(sid, computers):
    if not sid in session or "is_teacher" not in session[sid]:
        sio.disconnect(sid)
        return
    
    events_session = models.Session()
    database.session.add(events_session)
    database.session.commit()
    computers_status = {}

    for computer in computers:
        users = connected_computers[str(computer["id"])]

        variant = None
        if computer["type"] == 1:
            sio.emit(f'computer_{computer["id"]}_event', "first_point")
            variant = database.session.query(models.PracticeOneVariant).order_by(func.random()).first()

        new_event = models.Event(
            session_id=events_session.id,
            computer_id=computer["id"],
            type=computer["type"],
            mode=computer["mode"],
            practice_one_variant_id=variant.id,
            user_1_id=users[0]["id"],
            user_2_id=users[1]["id"] if len(users) > 1 else None
        )

        database.session.add(new_event)
        database.session.commit()

        sio.emit(f'computer_{computer["id"]}_event', {
            "event_id": new_event.id,
            "computer_id": computer["id"],
            "mode": computer["mode"],
            "type": computer["type"],
            "description": variant.description,
            "right_logist": variant.right_logist,
            "wrong_logist1": variant.wrong_logist1,
            "wrong_logist2": variant.wrong_logist2,
            "test": variant.test.to_json(),
            "bets": models.Bet.to_json_list(variant.bets)
        })

    sio.emit("session_id", events_session.id)

class CheckpointData:
    def __init__(self, event_id, step: int, points, fails: int):
        self.event_id = event_id
        self.points = points
        self.fails = fails
        self.step = step


def finish_event(sid, event_id):
    computer_id = session[sid]['computer_id']
    users_id = session[sid]['ids']
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    event.is_finished = True
    database.session.commit()
    users_result = []
    for user_id in users_id:
        result = session.query(func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails)).\
            filter(models.EventCheckpoint.event_id == event_id, models.EventCheckpoint.user_id == user_id).first()
        
        user = session.query(models.User).filter(models.User.id == user_id).first()

        users_result.append({
                    "id": user_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "group_name": user.student.group.name,
                    "points": result[0],
                    "fails": result[1]
                })

    sio.emit(f'computer_{computer_id}_results', users_result)


@sio.on('event_checkpoint')
def checkpoint(sid, checkpoint_data: CheckpointData):
    def event_checkpoint(event_id: int, user_id: int, step:int, points: int, fails: int, computer_id: int):
        checkpoint = models.EventCheckpoint(event_id=event_id, user_id=user_id, step=step, points=points, fails=fails)
        database.session.add(checkpoint)
        database.session.commit()
        step_name = database.session.query(models.PracticeOneStep).filter(models.PracticeOneStep.id == step).first().name
        computers_status[computer_id] = step_name

    if sid not in session or "ids" not in session[sid]:
        sio.disconnect(sid)
        return

    for user_id in session[sid]["ids"]:
        event_checkpoint(event_id=checkpoint_data.event_id, user_id=user_id,
                         step=checkpoint_data.step, points=checkpoint_data.points,
                         fails=checkpoint_data.fails, computer_id=session[sid]['computer_id'])
        
    sio.emit('events_status', computers_status)


@sio.on('finish_event')
def finish_event(sid, event_id):
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    event.is_finished = True
    

def start_socket_server():
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), app)
