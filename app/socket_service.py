import random
from typing import List

from sqlalchemy.sql.expression import func

import oauth2
import models
import database
import schemas

def validate_tokens(environ, session, sid):
    first_token = environ.get('HTTP_AUTHORIZATION')
    second_token = environ.get('HTTP_AUTHORIZATION_TWO')

    if not first_token or first_token == second_token:
        print("First token wasn't provided or tokens are the same", flush=True)
        return False, None, None, None, None

    user = oauth2.get_current_user_socket(first_token)
    if not user:
        print("User wasn't found", flush=True)
        return False, None, None, None, None

    computer_id = environ.get("HTTP_COMPUTER_ID")
    if not computer_id:
        print("Computer id wasn't provided", flush=True)
        return False, None, None, None, None
    
    session.setdefault(sid, {})
    
    if user.role == "TEACHER":
        session[sid]["is_teacher"] = True
        return True, user, int(computer_id), None, True

    user2 = None
    if second_token:
        user2 = oauth2.get_current_user_socket(second_token)
        if not user2:
            print("Second authorization token is not correct", flush=True)
            return False, None, None, None, None

    return True, user, int(computer_id), user2, False

def update_session(sid, session, connected_computers, user, user2, computer_id:int):
    connected_computers[computer_id] = [user.serialize()]
    user_ids = [user.id]
    user_usernames = [user.username]

    if user2:
        connected_computers[computer_id].append(user2.serialize())
        user_ids.append(user2.id)
        user_usernames.append(user2.username)

    session[sid]["ids"] = user_ids
    session[sid]["usernames"] = user_usernames
    session[sid]["computer_id"] = computer_id

def emit_connected_computers(sio, connected_computers):
    sio.emit('connected_computers', connected_computers)

def is_valid_teacher_session(sid, session):
    return sid in session and "is_teacher" in session[sid]

def create_events_session():
    events_session = models.Session()
    database.session.add(events_session)
    database.session.commit()
    return events_session

def create_event(session_id, computer, users, variant):
    new_event = models.Event(
        session_id=session_id,
        computer_id=computer["id"],
        type=computer["type"],
        mode=computer["mode"],
        practice_one_variant_id=variant.id,
        user_1_id=users[0]["id"],
        user_2_id=users[1]["id"] if len(users) > 1 else None
    )
    database.session.add(new_event)
    database.session.commit()
    return new_event

def get_random_practice_one_variant():
    return database.session.query(models.PracticeOneVariant).order_by(func.random()).first()

def get_all_bets():
    return database.session.query(models.Bet).all()

def get_random_incoterms():
    return random.sample(list(models.Incoterms), 9)

def emit_computer_event(sio, computer, event_id, variant):
    all_bets = get_all_bets()
    random_incoterms = get_random_incoterms()

    sio.emit(f'computer_{computer["id"]}_event', {
            "event_id": event_id,
            "computer_id": computer["id"],
            "mode": computer["mode"],
            "type": computer["type"],
            "description": variant.description,
            "right_logist": variant.right_logist,
            "wrong_logist1": variant.wrong_logist1,
            "wrong_logist2": variant.wrong_logist2,
            "test": variant.test.to_json(),
            "random_incoterms": random_incoterms,
            "all_bets": models.Bet.to_json_list(all_bets)
        })

def finish_event(sid, sio, session, event_id):
    computer_id = session[sid]['computer_id']
    users_id = session[sid]['ids']
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    event.is_finished = True
    database.session.commit()
    users_result = []
    for user_id in users_id:
        result = database.session.query(func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails)).\
            filter(models.EventCheckpoint.event_id == event_id, models.EventCheckpoint.user_id == user_id).first()
        
        user = database.session.query(models.User).filter(models.User.id == user_id).first()

        users_result.append({
                    "id": user_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "group_name": user.student.group.name,
                    "points": result[0],
                    "fails": result[1]
                })

    sio.emit(f'computer_{computer_id}_results', users_result)

def create_checkpoint(event_id, user_id, step_id, points, fails):
    checkpoint = models.EventCheckpoint(event_id=event_id, user_id=user_id, step_id=step_id, points=points, fails=fails)
    database.session.add(checkpoint)
    database.session.commit()

def create_users_checkpoints(sio, sid, session, checkpoint_data:schemas.CheckpointData, computers_status):
    users = []
    
    sio.emit('logs', checkpoint_data)

    for user_id in session[sid]["ids"]:
        create_checkpoint(event_id=checkpoint_data["event_id"], user_id=user_id,
                         step_id=checkpoint_data["step"], points=checkpoint_data["points"],
                         fails=checkpoint_data["fails"])
        
        user = database.session.query(models.User).filter(models.User.id == user_id).first().serialize()
        users.append(user)

        step_name = database.session.query(models.PracticeOneStep).filter(models.PracticeOneStep.id == checkpoint_data["step"]).first().name
        computer_id = session[sid]['computer_id']
        computers_status[computer_id] = {"step_name": step_name, "users": users}

def create_log(sio, endpoint:str, computer_id: int, user:models.User = None, id:int = None):
    if not user:
        user = database.session.query(models.User).filter(models.User.id == id).first().serialize()
        
    log = models.Log(user_id=user.id, endpoint=endpoint, computer_id=computer_id)
    database.session.add(log)
    database.session.commit()

    sio.emit('logs', f"{user.username} | {endpoint} | 'computer_id':{computer_id} | {log.created_at}")

def create_log_for_users(sio, endpoint:str, computer_id: int, users:List[models.User] = [], ids:List[str] = []):
    for user in users:
            create_log(sio, user, endpoint, computer_id)

    for user_id in ids:
        user = database.session.query(models.User).filter(models.User.id == user_id).first().serialize()
        create_log(sio, user, endpoint, computer_id)
