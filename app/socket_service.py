import math
import random
from typing import List, Tuple, Optional, Union

from sqlalchemy.sql.expression import func

import oauth2
import models
import database
import schemas
from utils import formatting_number as f


def validate_tokens(
    environ, session, sid
) -> Tuple[bool, Optional[models.User], Optional[int], Optional[models.User], Optional[bool]]:
    first_token = environ.get('HTTP_AUTHORIZATION')
    second_token = environ.get('HTTP_AUTHORIZATION_TWO')

    if not first_token or first_token == second_token:
        print("First token wasn't provided or tokens are the same", flush=True)
        return False, None, None, None, None

    user = oauth2.get_current_user_socket(first_token)
    if not user:
        print("User wasn't found", flush=True)
        return False, None, None, None, None

    computer_id = environ.get('HTTP_COMPUTER_ID')
    if not computer_id:
        print("Computer id wasn't provided", flush=True)
        return False, None, None, None, None

    session.setdefault(sid, {})

    if user.role == 'TEACHER':
        session[sid]['is_teacher'] = True
        session[sid]['ids'] = [user.id]
        session[sid]['computer_id'] = computer_id
        return True, user, int(computer_id), None, True

    user2 = None
    if second_token:
        user2 = oauth2.get_current_user_socket(second_token)
        if not user2:
            print('Second authorization token is not correct', flush=True)
            return False, None, None, None, None

    return True, user, int(computer_id), user2, False


def update_session(sid, session, connected_computers, user, user2, computer_id: int):
    connected_computers[computer_id] = [user.serialize()]
    user_ids = [user.id]
    user_usernames = [user.username]

    if user2:
        connected_computers[computer_id].append(user2.serialize())
        user_ids.append(user2.id)
        user_usernames.append(user2.username)

    session[sid]['ids'] = user_ids
    session[sid]['usernames'] = user_usernames
    session[sid]['computer_id'] = computer_id


def emit_connected_computers(sio, connected_computers):
    sio.emit('connected_computers', connected_computers)


def is_valid_teacher_session(sid, session):
    return sid in session and 'is_teacher' in session[sid]


def create_events_session():
    events_session = models.Session()
    database.session.add(events_session)
    database.session.commit()
    return events_session


def get_random_variant(type: int):
    if type == 1:
        return (
            database.session.query(models.PracticeOneVariant).order_by(func.random()).first()
        )
    if type == 2:
        return (
            database.session.query(models.PracticeTwoVariant).order_by(func.random()).first()
        )


def create_event(sio, session_id, computer, users):
    variant = get_random_variant(type=computer['type'])

    if not variant:
        sio.emit('errors', 'No random variant found')
        raise Exception('No random variant found')

    new_event = models.Event(
        session_id=session_id,
        computer_id=computer['id'],
        type=computer['type'],
        mode=computer['mode'],
        variant_one_id=variant.id if computer['type'] == 1 else None,
        variant_two_id=variant.id if computer['type'] == 2 else None,
        user_1_id=users[0]['id'],
        user_2_id=users[1]['id'] if len(users) > 1 else None,
    )
    database.session.add(new_event)
    database.session.commit()
    return new_event


def get_all_bets():
    return database.session.query(models.Bet).all()


def get_random_incoterms(num: int = 9):
    return random.sample(list(models.Incoterms), num)


def practice_two(variant:models.PracticeTwoVariant):
    bets = models.PracticeTwoVariantBet.to_json_list(variant.bets)

    unique_bets_by_to_and_from_fields = []
    unique_pairs = set()

    for bet in bets:
        pair = (bet['from'], bet['to'])
        if pair not in unique_pairs:
            unique_pairs.add(pair)
            unique_bets_by_to_and_from_fields.append(bet)

    for bet in unique_bets_by_to_and_from_fields:
        tons = bet['tons']
        package_tons = variant.package_tons
        bet[
            'forty_containers_count'
        ] = f'{tons}/(40*{package_tons})={int(tons / 40 * package_tons)}'
        bet['route'] = f'{bet["from"]} - {bet["to"]}'

    containers = models.Container.to_json_list(database.session.query(models.Container).all())

    container_first_table = []

    for c in containers:
        length = c['length']
        width = c['width']
        height = c['height']
        loading_volume = length * width * height
        package_length = variant.package_length
        package_width = variant.package_width
        package_height = variant.package_height
        transport_package_volume = package_length * package_width * package_height
        packages_in_container = math.ceil(
            math.floor(length / package_length)
            * math.floor(width / package_width)
            * math.floor(height / package_height)
        )
        size = c['size']
        payload_capacity = c['payload_capacity']

        container_first_table.append(
            {
                'type': f'{size}-футовый контейнер {length}м*{width}м*{height}м (Д*Ш*В), грузоподъёмность {payload_capacity}т',
                'loading_volume': f'{length}*{width}*{height}={f(loading_volume)}',
                'transport_package_volume': f'{package_length}*{package_width}*{package_height}={f(transport_package_volume)}',
                'packages_in_container': f'({length}/{package_length})*({width}/{package_width})*({height}/{package_height})={packages_in_container}',
                'capacity_utilization_rate': f'{f(packages_in_container)}*{f(transport_package_volume)}/{f(loading_volume)}={f(packages_in_container * transport_package_volume / loading_volume)}',
                'payload_utilization_rate': f'{packages_in_container}*{package_tons}/{payload_capacity}={f(packages_in_container * package_tons / payload_capacity)}',
            }
        )

    return {
        'legend': variant.legend,
        'bets': bets,
        'containers_one': container_first_table,
        'containers_two': unique_bets_by_to_and_from_fields,
    }


def emit_computer_event(
    sio,
    computer,
    event_id,
    variant: Union[models.PracticeOneVariant, models.PracticeTwoVariant],
):
    sio.emit('errors', str(variant))

    if computer['type'] == 1:
        all_bets = get_all_bets()
        random_incoterms = get_random_incoterms()

        sio.emit(
            f'computer_{computer["id"]}_event',
            {
                'event_id': event_id,
                'computer_id': computer['id'],
                'mode': computer['mode'],
                'type': computer['type'],
                'description': variant.description,
                'right_logist': variant.right_logist,
                'wrong_logist1': variant.wrong_logist1,
                'wrong_logist2': variant.wrong_logist2,
                'test': variant.test.to_json(),
                'random_incoterms': random_incoterms,
                'all_bets': models.Bet.to_json_list(all_bets),
            },
        )

    if computer['type'] == 2:

        sio.emit(
            f'computer_{computer["id"]}_event',
            practice_two(variant=variant)
        )


def finish_event(sid, sio, session, event_id):
    computer_id = session[sid]['computer_id']
    users_id = session[sid]['ids']
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    event.is_finished = True
    database.session.commit()
    users_result = []
    for user_id in users_id:
        result = (
            database.session.query(
                func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails)
            )
            .filter(
                models.EventCheckpoint.event_id == event_id,
                models.EventCheckpoint.user_id == user_id,
            )
            .first()
        )

        user = database.session.query(models.User).filter(models.User.id == user_id).first()

        users_result.append(
            {
                'id': user_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'group_name': user.student.group.name,
                'points': result[0],
                'fails': result[1],
            }
        )

    sio.emit(f'computer_{computer_id}_results', users_result)


def create_checkpoint(event_id, user_id, step_id, points, fails):
    checkpoint = models.EventCheckpoint(
        event_id=event_id, user_id=user_id, step_id=step_id, points=points, fails=fails
    )
    database.session.add(checkpoint)
    database.session.commit()


def create_users_checkpoints(
    sio, sid, session, checkpoint_data: schemas.CheckpointData, computers_status
):
    users = []

    sio.emit('logs', checkpoint_data)

    for user_id in session[sid]['ids']:
        create_checkpoint(
            event_id=checkpoint_data['event_id'],
            user_id=user_id,
            step_id=checkpoint_data['step'],
            points=checkpoint_data['points'],
            fails=checkpoint_data['fails'],
        )

        user = (
            database.session.query(models.User)
            .filter(models.User.id == user_id)
            .first()
            .serialize()
        )
        users.append(user)

        step_name = (
            database.session.query(models.PracticeOneStep)
            .filter(models.PracticeOneStep.id == checkpoint_data['step'])
            .first()
            .name
        )
        computer_id = session[sid]['computer_id']
        computers_status[computer_id] = {'step_name': step_name, 'users': users}


def create_log(sio, endpoint: str, computer_id: int, user: models.User = None, id: int = None):
    if not user and id is not None:
        user = database.session.query(models.User).filter(models.User.id == id).first()
    log = models.Log(user_id=user.id, endpoint=endpoint, computer_id=computer_id)
    database.session.add(log)
    database.session.commit()

    sio.emit(
        'logs',
        f"{user.username} | {endpoint} | 'computer_id':{computer_id} | {log.created_at}",
    )


def create_log_for_users(
    sio, endpoint: str, computer_id: int, users: List[models.User] = [], ids: List[str] = []
):
    for user in users:
        if user is not None:
            create_log(sio=sio, endpoint=endpoint, computer_id=computer_id, user=user)
