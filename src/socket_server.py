import math
import random
from typing import Optional, Dict, Tuple, Union, List

import eventlet
import socketio
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func
from sqlalchemy import desc

import models
import schemas
from core.config import settings
from schemas import CheckpointData
from services import oauth2
from services.actions_logger import ActionsLogger


class SocketServer:
    def __init__(self, db_session: DBSession, logger: bool = False, cors_allowed_origins: Optional[str] = '*'):
        self._sio = socketio.Server(cors_allowed_origins=cors_allowed_origins, logger=logger)
        self._app = socketio.WSGIApp(
            self._sio, static_files={'/': {'content_type': 'text/html', 'filename': 'index.html'}}
        )
        self._logger = ActionsLogger()
        self._db_session = db_session

        self._connected_computers = {}
        self._session = {}
        self._computers_status = {}
        self._events_session = None

        self._sio.on('connect', self._connect)
        self._sio.on('disconnect', self._disconnect)
        self._sio.on('start_events', self._start_events)
        self._sio.on('start_late_events', self._start_late_events)
        self._sio.on('raise_hand', self._raise_hand)
        self._sio.on('event_checkpoint', self._event_checkpoint)
        self._sio.on('logs', self._logs)
        # self._sio.on('join_to_session', self._join_to_session)
        self._sio.on('_get_connected_users_without_session', self._get_connected_users_without_session)
        self._sio.on('where_am_i', self._where_am_i)
        self._sio.on('wait', self._wait)
        self._sio.on('finish_current_session', self._finish_current_session)

    def run(self):
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), self._app)

    def _connect(self, sid: str, environ: Dict):
        try:
            is_teacher, computer_id, users = self.__validate_tokens_or_raise(environ=environ, sid=sid)

            self._logger.log(sio=self._sio, users=users, endpoint='connection', computer_id=computer_id)

            if not is_teacher:
                self.__update_connected_computers_and_session(
                    sid=sid, users=users, computer_id=computer_id,
                )

            self._sio.emit('connected_computers', self._connected_computers)
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _disconnect(self, sid):
        try:
            if sid not in self._session or 'ids' not in self._session[sid]:
                self._sio.emit('logs', 'Client without session was disconnected')
                return

            self._logger.log(
                sio=self._sio,
                endpoint='disconnect',
                computer_id=self._session[sid]['computer_id'],
                users_ids=self._session[sid]['ids'],
            )

            self.__remove_from_connected_computers(sid)

            self._sio.emit('connected_computers', self._connected_computers)
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _start_events(self, sid, computers):
        try:
            self.__raise_if_not_valid_input_start_events(sid, computers)
            # TODO Добавить проверку, что прошлые events завершены, либо завершить их
            self._events_session = self.__create_events_session()

            self._logger.log(
                sio=self._sio,
                endpoint='create_event',
                computer_id=self._session[sid]['computer_id'],
                users_ids=self._session[sid]['ids'],
            )

            self.__create_and_emit_events(computers)

            self.__update_computers_status(computers)
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _finish_current_session(self, sid, _msg):
        if not self._events_session:
            raise Exception("Current session was not found!")

        result = []
        for event in self._events_session.event:
            users_results = self.__finish_event_and_emit_results(sid=sid, event_id=event.id)
            result.extend(users_results)

        self._sio.emit("users_results", result)

    def _start_late_events(self, sid, computers):
        """Добавляем новый пк уже к созданной сессии ( Для опоздавшего, заходящего с нового ПК )"""

        self.__raise_if_not_valid_input_start_late_events(sid, computers)
        self.__create_and_emit_events(computers)
        self.__update_computers_status(computers, is_joining=True)

    def _wait(self, sid, message):
        wait_reason = message.get('wait_reason', 'Причина не указана')
        computers_ids = message.get('computers_ids', [])

        self.__raise_if_not_valid_teacher(sid=sid, extra_text='_wait')
        self.__raise_if_not_all_computers_connected(computers_ids=computers_ids)

        for computer_id in computers_ids:
            event_wait_point = models.EventWaitTimePoint(
                event_id=self._computers_status[computer_id]['event_id'], type='START'
            )
            self._db_session.add(event_wait_point)
            self._db_session.commit()

            self._sio.emit(f'computer_{computer_id}_wait', {'type': 'start', 'wait_reason': wait_reason})

    def _where_am_i(self, sid, _msg):
        if 'computer_id' not in self._session[sid]:
            raise Exception("Not started yet")

        computer_id = self._session[sid]['computer_id']
        computer_status = self._computers_status[computer_id]
        is_on_pause = self.__check_if_computer_on_pause(computer_id)

        self._sio.emit(
            f'computer_{computer_id}_in', {**computer_status, 'is_on_pause': is_on_pause}
        )

    def _get_connected_users_without_session(self, _sid, _msg):
        connected_users_without_session = []

        for computer in self._connected_computers:
            if computer['id'] not in self._computers_status:
                connected_users_without_session.extend(self._connected_computers[computer['id']])

        self._sio.emit('connected_users_without_session', connected_users_without_session)

    def _join_to_event(self, sid, join_info: schemas.JoinData):
        self.__raise_if_not_valid_input_join_to_session(sid, join_info.computer_id)
        user = self._db_session.query(models.User).filter(models.User.id == join_info.user_id)
        self._connected_computers[join_info.computer_id]['users'].append(user.serialize())

    def _raise_hand(self, sid, _):
        try:
            if sid not in self._session or 'ids' not in self._session[sid]:
                self._sio.disconnect(sid)
                return

            requester_computer_id = self._session[sid]['computer_id']

            self._sio.emit('help_notification', {'computer_id': requester_computer_id})
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _event_checkpoint(self, sid, checkpoint_data: CheckpointData):
        try:
            step_id, step_name, event_id = self.__create_users_checkpoints_finish_if_last(
                sid=sid, checkpoint_data=checkpoint_data
            )

            self._logger.log(
                sio=self._sio,
                endpoint=f'checkpoint. step_id = {step_id}, step_name = {step_name}, event_id = {event_id}',
                computer_id=self._session[sid]['computer_id'],
                users_ids=self._session[sid]['ids'],
            )

            self._sio.emit('events_status', self._computers_status)
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _logs(self, _sid, message):
        self._sio.emit('logs', message)

    def __check_if_computer_on_pause(self, computer_id: int):
        event_id = self._computers_status[computer_id]['event_id']

        last_time_point = (
            self._db_session.query(models.EventWaitTimePoint.event_id == event_id)
            .order_by(desc(models.EventWaitTimePoint.created_at))
            .one()
        )

        if not last_time_point or last_time_point.type == 'STOP':
            return False

        return True

    def __get_waited_time(self, event_id: int):
        wait_time_points = self._db_session.query(models.EventWaitTimePoint).filter(models.Event.id == event_id)

        total = None
        curr_start_time = None

        for point in wait_time_points:
            if point.type == 'START':
                curr_start_time = point.created_at
            if point.type == 'STOP' and curr_start_time:
                total += point.created_at - curr_start_time

        return total

    def __finish_event_and_emit_results(self, sid, event_id):
        computer_id = self._session[sid]['computer_id']
        users_ids = self._session[sid]['ids']
        event = self._db_session.query(models.Event).filter(models.Event.id == event_id).first()
        event.is_finished = True
        self._db_session.commit()
        users_results = []
        for user_id in users_ids:
            result = (
                self._db_session.query(func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails))
                .filter(models.EventCheckpoint.event_id == event_id, models.EventCheckpoint.user_id == user_id,)
                .first()
            )

            user = self._db_session.query(models.User).filter(models.User.id == user_id).first()

            users_results.append(
                {
                    'id': user_id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'surname': user.surname,
                    'group_name': user.student.group.name,
                    'points': result[0],
                    'fails': result[1],
                }
            )

        self._sio.emit(f'computer_{computer_id}_results', users_results)

        return users_results

    def __get_last_step_number(self, event_id: int):
        pr_type = self.__get_pr_type_by_event_id(event_id)
        if pr_type == 1:
            return self._db_session.query(models.PracticeOneStep).count()
        elif pr_type == 2:
            return self._db_session.query(models.PracticeTwoStep).count()

    def __get_previous_step_id(self, event_id: int):
        step = (
            self._db_session.query(models.EventCheckpoint)
            .order_by(desc(models.EventCheckpoint.created_at))
            .filter(models.EventCheckpoint.event_id == event_id)
            .first()
        )
        return step.id if step else 0

    def __get_pr_type_by_event_id(self, event_id: int):
        event = self._db_session.query(models.Event).filter(models.Event.id == event_id).first()
        return event.type if event else None

    def __create_checkpoint_to_db(self, event_id, user_id, step_id, points, fails):
        checkpoint = models.EventCheckpoint(
            event_id=event_id, user_id=user_id, step_id=step_id, points=points, fails=fails
        )
        self._db_session.add(checkpoint)
        self._db_session.commit()

    def __create_users_checkpoints_finish_if_last(self, sid, checkpoint_data: schemas.CheckpointData):
        computer_id = self._session[sid]['computer_id']
        event_id = self._computers_status[computer_id]['event_id']
        curr_step = self.__get_step(event_id=event_id)

        if checkpoint_data.step_id != curr_step.id:
            raise Exception(f"Current step_id should be : {curr_step.id}, but you sent {checkpoint_data.step_id}")

        users_ids = self._session[sid]['ids']
        last_step_id = self.__get_last_step_number(event_id)

        if len(users_ids) == 1 or curr_step.role in ['ALL', 'BUYER']:
            self.__create_checkpoint_to_db(
                event_id=event_id,
                user_id=users_ids[0],
                step_id=curr_step.id,
                points=checkpoint_data.points,
                fails=checkpoint_data.fails,
            )

        if len(users_ids) == 1 or curr_step.role in ['ALL', 'SELLER']:
            self.__create_checkpoint_to_db(
                event_id=event_id,
                user_id=users_ids[1] if len(users_ids) > 1 else users_ids[0],
                step_id=curr_step.id,
                points=checkpoint_data.points,
                fails=checkpoint_data.fails,
            )

        if curr_step.id == last_step_id:
            _ = self.__finish_event_and_emit_results(sid=sid, event_id=event_id)

        self._computers_status[computer_id]['step_name'] = curr_step.name
        self._computers_status[computer_id]['step_id'] = curr_step.id
        self._computers_status[computer_id]['role'] = curr_step.role

        return curr_step.id, curr_step.name, event_id

    def __get_step(self, event_id: int):
        event_type = self.__get_pr_type_by_event_id(event_id)
        step_id = self.__get_previous_step_id(event_id) + 1

        if event_type == 1:
            return self._db_session.query(models.PracticeOneStep).filter(models.PracticeOneStep.id == step_id)
        if event_type == 2:
            return self._db_session.query(models.PracticeTwoStep).filter(models.PracticeTwoStep.id == step_id)

    def __remove_from_connected_computers(self, sid):
        if 'is_teacher' not in self._session[sid]:
            del self._connected_computers[self._session[sid]['computer_id']]

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

    def __create_events_session(self):
        events_session = models.Session()
        self._db_session.add(events_session)
        self._db_session.commit()
        return events_session

    def __update_computers_status(self, computers, is_joining: bool = False):
        # Если случай с опоздавшим, то оставляем все как есть
        if not is_joining:
            self._computers_status = {}

        for computer in computers:
            users = self._connected_computers[computer['id']]
            self._computers_status[computer['id']] = {
                'step_name': 'start',
                'users': users,
                'step_id': 0,
                'event_id': computer['event_id'],
            }

    def __create_and_emit_events(self, computers):
        for computer in computers:
            users = self._connected_computers[computer['id']]

            new_event = self.__create_event(sio=self._sio, computer=computer, users=users)

            self.__emit_computer_event(
                computer=computer,
                event_id=new_event.id,
                variant=new_event.practice_one_variant if new_event.type == 1 else new_event.practice_two_variant,
            )

            computer['event_id'] = new_event.id

    def __create_event(self, sio, computer, users):
        variant = self.__get_random_variant(type=computer['type'])

        if not variant:
            sio.emit('errors', 'No random variant found')
            raise Exception('No random variant found')

        new_event = models.Event(
            session_id=self._events_session.id,
            computer_id=computer['id'],
            type=computer['type'],
            mode=computer['mode'],
            variant_one_id=variant.id if computer['type'] == 1 else None,
            variant_two_id=variant.id if computer['type'] == 2 else None,
            user_1_id=users[0]['id'],
            user_2_id=users[1]['id'] if len(users) > 1 else None,
        )
        self._db_session.add(new_event)
        self._db_session.commit()
        return new_event

    def __get_random_variant(self, type: int):
        if type == 1:
            return self._db_session.query(models.PracticeOneVariant).order_by(func.random()).first()
        if type == 2:
            return self._db_session.query(models.PracticeTwoVariant).order_by(func.random()).first()

    def __emit_computer_event(
        self, computer, event_id, variant: Union[models.PracticeOneVariant, models.PracticeTwoVariant],
    ):
        if computer['type'] == 1:
            all_bets = self.__get_all_bets()
            random_incoterms, incoterm_groups = self.__get_random_incoterm_groups()

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
                            total[key] = self.f(float(total[key]) + float(value))
                buyer_totals.append(total)

            for i in range(len(seller_tables)):
                total = {incoterm: buyer_totals[i][incoterm] for incoterm in incoterm_groups[i]}
                for bet in seller_tables[i]:
                    for key, value in bet.items():
                        if key in total:
                            total[key] = self.f(float(total[key]) + float(value))
                seller_totals.append(total)

            delivery_prices = []
            for i in range(len(seller_totals)):
                delivery_price = {}
                for key in seller_totals[i].keys():
                    delivery_price[key] = self.f(float(seller_totals[i][key]) - float(buyer_totals[i][key]))
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

            self._sio.emit(
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
            self._sio.emit(
                f'computer_{computer["id"]}_event',
                self.__practice_two(
                    variant=variant,
                    event_id=event_id,
                    computer_id=computer['id'],
                    event_mode=computer['mode'],
                    event_type=computer['type'],
                ),
            )

    def __practice_two(
        self, variant: models.PracticeTwoVariant, event_id: int, computer_id: int, event_mode, event_type: int
    ):
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

        containers = models.Container.to_json_list(self._db_session.query(models.Container).all())

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
                    'loading_volume': f'{length}*{width}*{height}={self.f(loading_volume)}',
                    'transport_package_volume': f'{package_length}*{package_width}*{package_height}={self.f(transport_package_volume)}',
                    'packages_in_container': f'({length}/{package_length})*({width}/{package_width})*({height}/{package_height})={packages_in_container}',
                    'capacity_utilization_rate': f'{self.f(packages_in_container)}*{self.f(transport_package_volume)}/{self.f(loading_volume)}={self.f(packages_in_container * transport_package_volume / loading_volume)}',
                    'payload_utilization_rate': f'{packages_in_container}*{package_tons}/{payload_capacity}={self.f(packages_in_container * package_tons / payload_capacity)}',
                }
            )

            routes_table = [
                {
                    'route': f'{bet["from"]} - {bet["to"]}',
                    'destination_route': f'{bet["from"]} - {bet["to"]} через {bet["through"]}',
                    'full_route': ' - '.join(
                        self._db_session.query(models.Point).filter(models.Point.id == point_id).first().name
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
                        self._db_session.query(models.Route)
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
                    point = self._db_session.query(models.Point).filter(models.Point.id == point_id).first()
                    points_types.add(point.type)

                all_risks = models.Risk.to_json_list(self._db_session.query(models.Risk).all())
                risks_answer = [risk['name'] for risk in all_risks if risk['type'] in points_types]
                all_risks = [risk['name'] for risk in all_risks]

                bets_days_risks.append(
                    {
                        'full_route': ' - '.join(
                            self._db_session.query(models.Point).filter(models.Point.id == point_id).first().name
                            for point_id in bet['answer']
                        ),
                        'days': {'answer': days, 'all_options': self.__get_random_days_options(days)},
                        'bets': {
                            'answer': third_party_bets,
                            'all_options': self.__get_random_bets_options(third_party_bets),
                        },
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

            overall = self.__overall_calculations(bets_calculations=countries_route_dict)

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

    def __find_optimal_option(self, bets_calculations, variant_num):
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

        amount = self.f(sum(route['amount'] for route in stack) / 1000)
        route_numbers = [str(route['route_number']) for route in stack]

        return f"{amount}: {'-'.join(route_numbers)}"

    def __find_option(self, PL_name, variant_num, bets_calculations):
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
                    last_row = {
                        'route_number': dic['route_number'],
                        'amount': dic.get('containers_num', 1) * dic['bet'],
                    }
            if count < variant_num:
                stack.append(last_row)

        amount = self.f(sum(route['amount'] for route in stack) / 1000)
        route_numbers = [str(route['route_number']) for route in stack]

        return f"{amount}: {'-'.join(route_numbers)}"

    def __overall_calculations(self, bets_calculations):
        optimal_solution1 = self.__find_optimal_option(bets_calculations=bets_calculations, variant_num=1)
        optimal_solution2 = self.__find_optimal_option(bets_calculations=bets_calculations, variant_num=2)

        PL1_variant1 = self.__find_option(PL_name='PL1', variant_num=1, bets_calculations=bets_calculations)
        PL1_variant2 = self.__find_option(PL_name='PL1', variant_num=2, bets_calculations=bets_calculations)

        PL2_variant1 = self.__find_option(PL_name='PL2', variant_num=1, bets_calculations=bets_calculations)
        PL2_variant2 = self.__find_option(PL_name='PL2', variant_num=2, bets_calculations=bets_calculations)

        PL3_variant1 = self.__find_option(PL_name='PL3', variant_num=1, bets_calculations=bets_calculations)
        PL3_variant2 = self.__find_option(PL_name='PL3', variant_num=2, bets_calculations=bets_calculations)

        return {
            '3PL1': {'first': PL1_variant1, 'second': PL1_variant2},
            '3PL2': {'first': PL2_variant1, 'second': PL2_variant2},
            '3PL3': {'first': PL3_variant1, 'second': PL3_variant2},
            'optimal': {'first': optimal_solution1, 'second': optimal_solution2},
        }

    @staticmethod
    def __get_random_days_options(days: int):
        s = {days}
        for _ in range(15):
            num = random.randint(days - 20, days + 30)
            if num > 1:
                s.add(num)
        return list(s)

    @staticmethod
    def __get_random_bets_options(bets: list):
        s = set(bets)
        for _ in range(15):
            num = random.randint(bets[0] / 100 - 20, bets[0] / 100 + 40)
            if num > 5:
                s.add(num * 100)
        return list(s)

    @staticmethod
    def __get_random_incoterm_groups():
        """Returns chosen incoterms and 3 incoterm groups divided by 3"""
        incoterms = [incoterm.value for incoterm in random.sample(list(models.Incoterms), 9)]

        incoterm_groups = [incoterms[i : i + 3] for i in range(0, len(incoterms), 3)]

        return incoterms, incoterm_groups

    def __get_all_bets(self):
        return self._db_session.query(models.Bet).all()

    def __raise_if_not_valid_input_start_events(self, sid, computers):
        self.__raise_if_not_valid_start_events_input(computers)
        self.__raise_if_not_all_computers_connected(computers)
        self.__raise_if_not_valid_teacher(sid=sid, extra_text='start_events endpoint')

    def __raise_if_not_valid_input_start_late_events(self, sid, computers):
        self.__raise_if_not_valid_teacher(sid=sid, extra_text='start_late_events endpoint')
        self.__raise_if_not_valid_start_events_input(computers)
        self.__raise_if_not_all_computers_connected(computers)
        self.__raise_if_computers_already_started(computers=computers)

    def __raise_if_not_valid_input_join_to_session(self, sid, computer_id):
        self.__raise_if_not_valid_teacher(sid=sid, extra_text='join_to_session endpoint')
        self.__raise_if_computer_not_connected_or_busy(computer_id)

    @staticmethod
    def __raise_if_not_valid_start_events_input(computers):
        for computer in computers:
            schemas.StartEventComputer(**computer)

    def __raise_if_computer_not_connected_or_busy(self, computer_id):
            if computer_id not in self._connected_computers:
                raise Exception(f'Computer with id {computer_id} is not connected')

            users = self._connected_computers[computer_id]
            if len(users) > 1:
                raise Exception(f"Maxumum spots are busy on computer with number {computer_id}")

    def __raise_if_not_all_computers_connected(self, computers=None, computers_ids=None):
        if computers is None and computers_ids is None:
            raise Exception('Not valid parameters in __raise_if_not_all_computers_connected')

        if computers_ids:
            for computer_id in computers_ids:
                if computer_id not in self._connected_computers:
                    raise Exception(f'Компьютер с номером {computer_id} не подключен')
        else:
            for computer in computers:
                if computer['id'] not in self._connected_computers:
                    raise Exception(f'Компьютер с номером {computer["id"]} не подключен')

    def __raise_if_not_valid_teacher(self, sid, extra_text):
        if not (sid in self._session and 'is_teacher' in self._session[sid]):
            raise Exception('Not valid teacher ' + extra_text)

    def __raise_if_computers_already_started(self, computers):
        for computer in computers:
            computer_num = int(computer['id'])
            if computer_num in self._connected_computers:
                raise Exception(f'Computer with number {computer_num} is already started')

    @staticmethod
    def f(num):
        """Formats a number without trailing zeros at the end.

            Examples:

            >>> f(3)
            '3'

            >>> f(3.456412)
            '3.45'

            >>> f(3.1)
            '3.1'
            """

        rounded_num = round(num, 2)
        if rounded_num.is_integer() or rounded_num * 100 % 100 == 0:
            return f'{rounded_num:.0f}'
        elif rounded_num * 100 % 10 == 0:
            return f'{rounded_num:.1f}'
        else:
            return f'{rounded_num:.2f}'
