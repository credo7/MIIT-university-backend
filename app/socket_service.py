import json
import math
import random
from typing import List, Optional, Tuple, Union

import database
import models
import oauth2
import schemas
from sqlalchemy.sql.expression import func
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
        return database.session.query(models.PracticeOneVariant).order_by(func.random()).first()
    if type == 2:
        return database.session.query(models.PracticeTwoVariant).order_by(func.random()).first()


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


def get_random_incoterm_groups():
    """Returns chosen incoterms and 3 incoterm groups divided by 3"""
    incoterms = [incoterm.value for incoterm in random.sample(list(models.Incoterms), 9)]

    incoterm_groups = [incoterms[i : i + 3] for i in range(0, len(incoterms), 3)]

    return incoterms, incoterm_groups


def get_random_days_options(days: int):
    s = set([days])
    for _ in range(15):
        num = random.randint(days - 20, days + 30)
        if num > 1:
            s.add(num)
    return list(s)


def get_random_bets_options(bets: list):
    s = set(bets)
    for _ in range(15):
        num = random.randint(bets[0] / 100 - 20, bets[0] / 100 + 40)
        if num > 5:
            s.add(num * 100)
    return list(s)


def find_option(PL_name, variant_num, bets_calculations):
    stack = []
    for val in bets_calculations.values():
        count = 0
        last_row = None
        for dic in val:
            if PL_name in dic['full_route_name']:
                count += 1
                if variant_num == count:
                    stack.append(
                        {'route_number': dic['route_number'], 'amount': dic.get('containers_num', 1) * dic['bet']}
                    )
                    break
                last_row = {'route_number': dic['route_number'], 'amount': dic.get('containers_num', 1) * dic['bet']}
        if count < variant_num:
            stack.append(last_row)

    amount = f(sum(route['amount'] for route in stack) / 1000)
    route_numbers = [str(route['route_number']) for route in stack]

    return f"{amount}: {'-'.join(route_numbers)}"


def find_optimal_option(bets_calculations, variant_num):
    stack = []
    for val in bets_calculations.values():
        curr_minimal_num = float('inf')
        curr_minimal = None
        for dic in val:
            if curr_minimal_num > dic['bet']:
                curr_minimal_num = dic['bet']
                curr_minimal = {
                    'route_number': dic['route_number'],
                    'amount': dic.get('containers_num', 1) * dic['bet'],
                }
            if variant_num == 2 and curr_minimal_num == dic['bet']:
                curr_minimal = {
                    'route_number': dic['route_number'],
                    'amount': dic.get('containers_num', 1) * dic['bet'],
                }
        stack.append(curr_minimal)

    amount = f(sum(route['amount'] for route in stack) / 1000)
    route_numbers = [str(route['route_number']) for route in stack]

    return f"{amount}: {'-'.join(route_numbers)}"


def overall_calculations(bets_calculations):
    optimal_solution1 = find_optimal_option(bets_calculations=bets_calculations, variant_num=1)
    optimal_solution2 = find_optimal_option(bets_calculations=bets_calculations, variant_num=2)

    PL1_variant1 = find_option(PL_name='PL1', variant_num=1, bets_calculations=bets_calculations)
    PL1_variant2 = find_option(PL_name='PL1', variant_num=2, bets_calculations=bets_calculations)

    PL2_variant1 = find_option(PL_name='PL2', variant_num=1, bets_calculations=bets_calculations)
    PL2_variant2 = find_option(PL_name='PL2', variant_num=2, bets_calculations=bets_calculations)

    PL3_variant1 = find_option(PL_name='PL3', variant_num=1, bets_calculations=bets_calculations)
    PL3_variant2 = find_option(PL_name='PL3', variant_num=2, bets_calculations=bets_calculations)

    return {
        '3PL1': {'first': PL1_variant1, 'second': PL1_variant2},
        '3PL2': {'first': PL2_variant1, 'second': PL2_variant2},
        '3PL3': {'first': PL3_variant1, 'second': PL3_variant2},
        'optimal': {'first': optimal_solution1, 'second': optimal_solution2},
    }


def practice_two(variant: models.PracticeTwoVariant, event_id: int, computer_id: int, event_mode, event_type: int):
    bets = models.PracticeTwoVariantBet.to_json_list(variant.bets)

    unique_bets_by_to_and_from_fields = []
    unique_pairs = set()

    for bet in bets:
        pair = (bet['from'], bet['to'])
        if pair not in unique_pairs:
            unique_pairs.add(pair)
            unique_bets_by_to_and_from_fields.append(bet)

    containers_two_description = '\n'.join(
        [f'{bet["from"]} - {bet["to"]} {bet["tons"]} т/месяц' for bet in unique_bets_by_to_and_from_fields]
    )

    containers_two_description = (
        f'На основании изучения рынка и заключённых договоров на поставку продукции '
        f'сформированы {len(unique_bets_by_to_and_from_fields)} новых цепей поставок '
        f'продукции ежемесячно при разных условиях Инкотермс:\n' + containers_two_description
    )

    for bet in unique_bets_by_to_and_from_fields:
        tons = bet['tons']
        package_tons = variant.package_tons
        bet['forty_containers_count'] = f'{tons}/(40*{package_tons})={int(tons / 40 * package_tons)}'
        bet['route '] = f'{bet["from"]} - {bet["to"]}'

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

        routes_table = [
            {
                'route': f'{bet["from"]} - {bet["to"]}',
                'destination_route': f'{bet["from"]} - {bet["to"]} через {bet["through"]}',
                'full_route': ' - '.join(
                    database.session.query(models.Point).filter(models.Point.id == point_id).first().name
                    for point_id in bet['answer']
                ),
            }
            for bet in bets
        ]

        bets_days_risks = []

        for bet in bets:
            answer: list = bet['answer']

            days = 0

            for i in range(len(answer) - 1):
                route = (
                    database.session.query(models.Route)
                    .filter(models.Route.from_point_id == answer[i], models.Route.to_point_id == answer[i + 1],)
                    .first()
                )
                days += route.days

            third_party_bets = [
                bet.get('3PL1', None),
                bet.get('3PL2', None),
                bet.get('3PL3', None),
            ]

            third_party_bets = [bet for bet in third_party_bets if bet]

            points_types = set(['ALL'])
            for point_id in answer:
                point = database.session.query(models.Point).filter(models.Point.id == point_id).first()
                points_types.add(point.type)

            all_risks = models.Risk.to_json_list(database.session.query(models.Risk).all())
            risks_answer = [risk['name'] for risk in all_risks if risk['type'] in points_types]
            all_risks = [risk['name'] for risk in all_risks]

            bets_days_risks.append(
                {
                    'full_route': ' - '.join(
                        database.session.query(models.Point).filter(models.Point.id == point_id).first().name
                        for point_id in bet['answer']
                    ),
                    'days': {'answer': days, 'all_options': get_random_days_options(days)},
                    'bets': {'answer': third_party_bets, 'all_options': get_random_bets_options(third_party_bets),},
                    'risks': {'answer': risks_answer, 'all_options': all_risks},
                }
            )

            countries_route_dict = {}
            route_number = 1
            country_route_name_count = {}

            for bet in bets:
                route_name = f"{bet['from']} - {bet['to']}"
                if route_name not in country_route_name_count:
                    country_route_name_count[route_name] = [{}, {}, {}]

                PL1, PL2, PL3 = bet['3PL1'], bet['3PL2'], bet['3PL3']
                containers_num = math.ceil(bet['tons'] / (40 * bet['package_tons']))

                PLS = []

                if PL1:
                    PLS.append(
                        {
                            'full_route_name': '3PL1',
                            'bet': PL1,
                            'amount': f'{PL1}*{containers_num}={PL1 * containers_num}',
                            'containers_num': containers_num,
                            'route_number': route_number,
                        }
                    )

                    route_number += 1
                if PL2:
                    PLS.append(
                        {
                            'full_route_name': '3PL2',
                            'bet': PL2,
                            'amount': f'{PL2}*{containers_num}={PL2 * containers_num}',
                            'containers_num': containers_num,
                            'route_number': route_number,
                        }
                    )

                    route_number += 1
                if PL3:
                    PLS.append(
                        {
                            'full_route_name': '3PL3',
                            'bet': PL3,
                            'amount': f'{PL3}*{containers_num}={PL3 * containers_num}',
                            'containers_num': containers_num,
                            'route_number': route_number,
                        }
                    )

                    route_number += 1

                PLS[0]['full_route_name'] = (
                    f"{bet['from']} - {bet['to']} через {bet['through']} " + PLS[0]['full_route_name']
                )

                PLS = [PL for PL in PLS if PL]

                if route_name not in countries_route_dict:
                    countries_route_dict[route_name] = PLS
                else:
                    countries_route_dict[route_name].extend(PLS)

        overall = overall_calculations(bets_calculations=countries_route_dict)

    return {
        'event_id': event_id,
        'computer_id': computer_id,
        'mode': event_mode,
        'type': event_type,
        'legend': variant.legend,
        'bets': bets,
        'containers_one': container_first_table,
        'containers_two': {'description': containers_two_description, 'rows': unique_bets_by_to_and_from_fields,},
        'routes_table': routes_table,
        'bets_days_risks': bets_days_risks,
        'bets_calculations': countries_route_dict,
        'overall_calculations': overall,
    }


def emit_computer_event(
    sio, computer, event_id, variant: Union[models.PracticeOneVariant, models.PracticeTwoVariant],
):
    sio.emit('errors', str(variant))

    if computer['type'] == 1:
        all_bets = get_all_bets()
        random_incoterms, incoterm_groups = get_random_incoterm_groups()

        bets = models.Bet.to_json_list(all_bets)

        buyer_tables = []
        seller_tables = []
        for incoterms_group in incoterm_groups:
            buyer_table = []
            seller_table = []
            for bet in bets:
                buyer_dict = {}
                seller_dict = {}
                for bet_inctoterm in bet['incoterms']:
                    if bet_inctoterm['name'] in incoterms_group and bet_inctoterm['role'] != 'SELLER':
                        buyer_dict[bet_inctoterm['name']] = bet['rate']
                    if bet_inctoterm['name'] in incoterms_group and bet_inctoterm['role'] != 'BUYER':
                        seller_dict[bet_inctoterm['name']] = bet['rate']
                if buyer_dict:
                    buyer_table.append({'name': bet['name'], 'price': bet['rate'], **buyer_dict})
                if seller_dict:
                    seller_table.append({'name': bet['name'], 'price': bet['rate'], **seller_dict})
            buyer_tables.append(buyer_table)
            seller_tables.append(seller_table)

        buyer_totals = []
        seller_totals = []

        for i in range(len(buyer_tables)):
            total = {incoterm: variant.product_price for incoterm in incoterm_groups[i]}
            for bet in buyer_tables[i]:
                for key, value in bet.items():
                    if key in total:
                        total[key] = f(float(total[key]) + float(value))
            buyer_totals.append(total)

        for i in range(len(seller_tables)):
            total = {incoterm: buyer_totals[i][incoterm] for incoterm in incoterm_groups[i]}
            for bet in seller_tables[i]:
                for key, value in bet.items():
                    if key in total:
                        total[key] = f(float(total[key]) + float(value))
            seller_totals.append(total)

        delivery_prices = []
        for i in range(len(seller_totals)):
            delivery_price = {}
            for key in seller_totals[i].keys():
                delivery_price[key] = f(float(seller_totals[i][key]) - float(buyer_totals[i][key]))
            delivery_prices.append(delivery_price)

        options = [
            {'contract_price': buyer_totals[i], 'delivery_price': delivery_prices[i], 'total': seller_totals[i]}
            for i in range(3)
        ]

        min_option_total = float('inf')
        for option in options:
            curr_option_total = sum([float(num) for num in option['total'].values()])
            if curr_option_total < min_option_total:
                min_option_total = curr_option_total

        for i in range(len(options)):
            if sum([float(num) for num in options[i]['total'].values()]) == min_option_total:
                options[i]['is_correct'] = True
            else:
                options[i]['is_correct'] = False

        sio.emit(
            f'computer_{computer["id"]}_event',
            {
                'event_id': event_id,
                'computer_id': computer['id'],
                'mode': computer['mode'],
                'type': computer['type'],
                'legend': variant.legend,
                'product_price': variant.product_price,
                'buyer_table_1': {'rows': buyer_tables[0], 'total': buyer_totals[0]},
                'buyer_table_2': {'rows': buyer_tables[1], 'total': buyer_totals[1]},
                'buyer_table_3': {'rows': buyer_tables[2], 'total': buyer_totals[2]},
                'seller_table_1': {
                    'rows': seller_tables[0],
                    'contract_price': buyer_totals[0],
                    'delivery_price': delivery_prices[0],
                    'total': seller_totals[0],
                },
                'seller_table_2': {
                    'rows': seller_tables[1],
                    'contract_price': buyer_totals[1],
                    'delivery_price': delivery_prices[1],
                    'total': seller_totals[1],
                },
                'seller_table_3': {
                    'rows': seller_tables[2],
                    'contract_price': buyer_totals[2],
                    'delivery_price': delivery_prices[2],
                    'total': seller_totals[2],
                },
                'options': options,
                'test': variant.test.to_json(),
                'random_incoterms': random_incoterms,
                'all_bets': models.Bet.to_json_list(all_bets),
            },
        )

    if computer['type'] == 2:

        sio.emit(
            f'computer_{computer["id"]}_event',
            practice_two(
                variant=variant,
                event_id=event_id,
                computer_id=computer['id'],
                event_mode=computer['mode'],
                event_type=computer['type'],
            ),
        )


def get_pr_type_by_event_id(event_id: int):
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    return event.type if event else None


def finish_event(sid, sio, session, event_id):
    computer_id = session[sid]['computer_id']
    users_id = session[sid]['ids']
    event = database.session.query(models.Event).filter(models.Event.id == event_id).first()
    event.is_finished = True
    database.session.commit()
    users_result = []
    for user_id in users_id:
        result = (
            database.session.query(func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails))
            .filter(models.EventCheckpoint.event_id == event_id, models.EventCheckpoint.user_id == user_id,)
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
    checkpoint = models.EventCheckpoint(event_id=event_id, user_id=user_id, step_id=step_id, points=points, fails=fails)
    database.session.add(checkpoint)
    database.session.commit()


def create_users_checkpoints(sio, sid, session, checkpoint_data: schemas.CheckpointData, computers_status):
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

        user = database.session.query(models.User).filter(models.User.id == user_id).first().serialize()
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
        'logs', f"{user.username} | {endpoint} | 'computer_id':{computer_id} | {log.created_at}",
    )


def create_log_for_users(sio, endpoint: str, computer_id: int, users: List[models.User] = [], ids: List[str] = []):
    for user in users:
        if user is not None:
            create_log(sio=sio, endpoint=endpoint, computer_id=computer_id, user=user)
