import math
import random
from typing import Optional, Dict, Tuple, Union
from bson import ObjectId
from datetime import datetime

import eventlet
import socketio
from pymongo.database import Database
import pymongo

from db.mongo import get_db, CollectionNames, get_mongo_client
import schemas
from core.config import settings
from schemas import CheckpointData
from services import oauth2
from services.actions_logger import ActionsLogger


class SocketServer:
    def __init__(self, logger: bool = False, cors_allowed_origins: Optional[str] = '*'):
        self._sio = socketio.Server(cors_allowed_origins=cors_allowed_origins, logger=logger)
        self._app = socketio.WSGIApp(
            self._sio, static_files={'/': {'content_type': 'text/html', 'filename': 'index.html'}}
        )
        self._logger = ActionsLogger()
        self._db: Database = get_db()

        self._connected_computers = {}
        self._session = {}
        self._computers_status = {}
        self._events_session_id = None

        self._sio.on('connect', self._connect)
        self._sio.on('disconnect', self._disconnect)
        self._sio.on('start_events', self._start_events)
        self._sio.on('start_late_events', self._start_late_events)
        self._sio.on('raise_hand', self._raise_hand)
        self._sio.on('event_checkpoint', self._event_checkpoint)
        self._sio.on('logs', self._logs)
        self._sio.on('join_to_session', self._join_to_event)
        self._sio.on('_get_connected_users_without_session', self._get_connected_users_without_session)
        self._sio.on('where_am_i', self._where_am_i)
        # self._sio.on('wait', self._wait)
        self._sio.on('finish_current_session', self._finish_current_session)

    def run(self):
        eventlet.wsgi.server(eventlet.listen(('0.0.0.0', settings.socket_port)), self._app)

    def _connect(self, sid: str, environ: Dict):
        try:
            is_teacher, computer_id, user1, user2 = self.__validate_tokens_or_raise(environ=environ, sid=sid)

            self._logger.log(sio=self._sio, users=[user1, user2], endpoint='connection', computer_id=computer_id)

            if not is_teacher:
                self.__update_connected_computers_and_session(
                    sid=sid, user1=user1, user2=user2, computer_id=computer_id,
                )

            self._sio.emit('connected_computers', self._connected_computers)
        except Exception as e:
            self._sio.emit('errors', str(e))
            self._sio.disconnect(sid)

    def _disconnect(self, sid):
        # try:
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
        # except Exception as e:
        #     self._sio.emit('errors', str(e))
        #     self._sio.disconnect(sid)

    def _start_events(self, sid, computers):
        # try:
        self.__raise_if_not_valid_input_start_events(sid, computers)
        # TODO Добавить проверку, что прошлые events завершены, либо завершить их
        self._events_session_id = self.__create_events_session()

        self._logger.log(
            sio=self._sio,
            endpoint='create_event',
            computer_id=self._session[sid]['computer_id'],
            users_ids=self._session[sid]['ids'],
        )

        self.__create_and_emit_events(computers)

        self.__update_computers_status(computers)
        # except Exception as e:
        #     self._sio.emit('errors', str(e))
        #     self._sio.disconnect(sid)

    def _finish_current_session(self, sid, _msg):
        if not self._events_session_id:
            raise Exception("Current session was not found!")

        result = []
        current_events = self._db[CollectionNames.EVENTS.value].find({
            "session_id" : self._events_session_id
        })
        for event in current_events:
            users_results = self.__finish_event_and_emit_results(sid=sid, event_id=event.id)
            result.extend(users_results)

        self._sio.emit("users_results", result)

    def _start_late_events(self, sid, computers):
        """Добавляем новый пк уже к созданной сессии ( Для опоздавшего, заходящего с нового ПК )"""

        self.__raise_if_not_valid_input_start_late_events(sid, computers)
        self.__create_and_emit_events(computers)
        self.__update_computers_status(computers, is_joining=True)

    # def _wait(self, sid, message):
    #     wait_reason = message.get('wait_reason', 'Причина не указана')
    #     computers_ids = message.get('computers_ids', [])
    #
    #     self.__raise_if_not_valid_teacher(sid=sid, extra_text='_wait')
    #     self.__raise_if_not_all_computers_connected(computers_ids=computers_ids)
    #
    #     for computer_id in computers_ids:
    #         event_wait_point = models.EventWaitTimePoint(
    #             event_id=self._computers_status[computer_id]['event_id'], type='START'
    #         )
    #         self._db_session.add(event_wait_point)
    #         self._db_session.commit()
    #
    #         self._sio.emit(f'computer_{computer_id}_wait', {'type': 'start', 'wait_reason': wait_reason})

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
        user = self._db[CollectionNames.USERS.value].find_one({"_id": ObjectId(join_info.user_id)})
        self._connected_computers[join_info.computer_id]['users'].append(schemas.UserOut.mongo_to_json(user))

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

    # def __check_if_computer_on_pause(self, computer_id: int):
    #     event_id = self._computers_status[computer_id]['event_id']
    #
    #     last_time_point = (
    #         self._db_session.query(models.EventWaitTimePoint.event_id == event_id)
    #         .order_by(desc(models.EventWaitTimePoint.created_at))
    #         .one()
    #     )
    #
    #     if not last_time_point or last_time_point.type == 'STOP':
    #         return False
    #
    #     return True

    # def __get_waited_time(self, event_id: int):
    #     wait_time_points = self._db_session.query(models.EventWaitTimePoint).filter(models.Event.id == event_id)
    #
    #     total = None
    #     curr_start_time = None
    #
    #     for point in wait_time_points:
    #         if point.type == 'START':
    #             curr_start_time = point.created_at
    #         if point.type == 'STOP' and curr_start_time:
    #             total += point.created_at - curr_start_time
    #
    #     return total

    def __create_events_session(self):
        session_id = str(self._db[CollectionNames.EVENTS_SESSION.value].insert_one({
            "created_at": datetime.now()
        }).inserted_id)
        return session_id

    def __finish_event_and_emit_results(self, sid, event_id):
        computer_id = self._session[sid]['computer_id']
        users_ids = self._session[sid]['ids']
        self._db[CollectionNames.EVENTS.value].update_one({
            "_id": ObjectId(event_id)
        }, {"$set":{"is_finished": True}})

        users_results = []
        for user_id in users_ids:
            checkpoints = self._db[CollectionNames.CHECKPOINTS.value].find_one({
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            result = {"points": 0, "fails": 0}
            for checkpoint in checkpoints:
                if checkpoint["points"]:
                    result["points"] += checkpoint["points"]
                if checkpoint["fails"]:
                    result["fails"] += checkpoint["fails"]

            event = self._db[CollectionNames.EVENTS.value].find_one({"_id"})

            user_update_operation = {
                "$inc":{
                    "points": result["points"]
                },
                "$push":{
                    "completed_pr1_variants" if event["type"] == 1 else "completed_pr2_variants": event["variant_id"]
                },
            }

            user = self._db[CollectionNames.USERS.value].find_one_and_update({
                "_id": ObjectId(user_id)
            }, user_update_operation)

            users_results.append(
                {
                    'id': user_id,
                    'first_name': user["first_name"],
                    'last_name': user["last_name"],
                    'surname': user["surname"],
                    'group_name': user["group_name"],
                    'points': result["points"],
                    'fails': result["fails"],
                }
            )

        self._sio.emit(f'computer_{computer_id}_results', users_results)

        return users_results

    def __get_last_step_index(self, event_id: str):
        event = self._db[CollectionNames.EVENTS.value].find_one({"_id": ObjectId(event_id)})
        if event["type"] == 1:
            return self._db[CollectionNames.PR1_STEPS.value].count_documents({})
        elif event["type"] == 2:
            return self._db[CollectionNames.PR2_STEPS.value].count_documents({})

    def __create_checkpoint_to_db(self, event_id, user_id, step_id, points, fails):
        checkpoint = {
            "event_id": event_id,
            "user_id": user_id,
            "step_id": step_id,
            "points": points,
            "fails": fails
        }

        self._db[CollectionNames.CHECKPOINTS.value].insert_one(checkpoint)

    def __create_users_checkpoints_finish_if_last(self, sid, checkpoint_data: schemas.CheckpointData):
        computer_id = self._session[sid]['computer_id']
        event_id = self._computers_status[computer_id]['event_id']
        curr_step = self.__get_step(event_id=event_id)

        if checkpoint_data.step_index != curr_step["index"]:
            raise Exception(f"Current step_id should be : {curr_step['index']}, but you sent {checkpoint_data.step_index}")

        users_ids = self._session[sid]['ids']
        last_step_index = self.__get_last_step_index(event_id)

        if len(users_ids) == 1 or curr_step["role"] in ['ALL', 'BUYER']:
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

        if curr_step["index"] == last_step_index:
            self.__finish_event_and_emit_results(sid=sid, event_id=event_id)

        self._computers_status[computer_id]['step_name'] = curr_step.name
        self._computers_status[computer_id]['step_id'] = curr_step.id
        self._computers_status[computer_id]['role'] = curr_step.role

        return curr_step.id, curr_step.name, event_id

    def __get_step(self, event_id: str):
        event = self._db[CollectionNames.EVENTS.value].find_one({"_id": ObjectId(event_id)})
        checkpoint = self._db[CollectionNames.CHECKPOINTS.value].find_one({"event_id": ObjectId(event_id)}, sort=[("step_index", pymongo.DESCENDING)])
        step_index = checkpoint["step_index"] + 1

        if event["type"] == 1:
            return self._db[CollectionNames.PR1_STEPS.value].find_one({"index": step_index})
        if event["type"] == 2:
            return self._db[CollectionNames.PR2_STEPS.value].find_one({"index": step_index})

    def __remove_from_connected_computers(self, sid):
        if 'is_teacher' not in self._session[sid]:
            del self._connected_computers[self._session[sid]['computer_id']]

    def __validate_tokens_or_raise(
        self, sid, environ
    ) -> Tuple[bool, Optional[int], Optional[Dict], Optional[Dict]]:
        """Function checks if computer id is set, if user is Teacher, if tokens are valid or raise an Exception."""

        first_token = environ.get('HTTP_AUTHORIZATION')
        second_token = environ.get('HTTP_AUTHORIZATION_TWO')

        if not first_token or first_token == second_token:
            raise Exception("First token wasn't provided or tokens are the same")

        user = oauth2.get_current_user_socket(first_token)
        if not user:
            raise Exception("User wasn't found")

        if not user["approved"]:
            raise Exception("User wasn't approved")

        computer_id = environ.get('HTTP_COMPUTER_ID')
        if not computer_id:
            raise Exception("Computer id wasn't provided")

        self._session.setdefault(sid, {})

        if user["role"] == 'TEACHER':
            self._session[sid]['is_teacher'] = True
            self._session[sid]['ids'] = [user["_id"]]
            self._session[sid]['computer_id'] = computer_id
            return True, int(computer_id), user, None

        user2 = None
        if second_token:
            user2 = oauth2.get_current_user_socket(second_token)
            if not user2:
                raise Exception('Second authorization token is not correct')
            if not user2.approved:
                raise Exception("Second user wasn't approved")

        return False, int(computer_id), user, user2

    def __update_connected_computers_and_session(self, sid, user1, user2, computer_id: int):
        self._connected_computers[computer_id] = [user1]
        user_ids = [user1["_id"]]
        user_usernames = [user1["username"]]

        if user2:
            self._connected_computers[computer_id].append(user2)
            user_ids.append(user2["_id"])
            user_usernames.append(user2["username"])

        self._session[sid]['ids'] = user_ids
        self._session[sid]['usernames'] = user_usernames
        self._session[sid]['computer_id'] = computer_id

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
                event_id=new_event["_id"],
                variant_id=new_event["variant_id"]
            )

            computer['event_id'] = new_event["_id"]

    def __create_event(self, sio, computer, users):
        variant_id = self.__get_random_variant_id(type=computer['type'])

        if not variant_id:
            sio.emit('errors', 'No random variant found')
            raise Exception('No random variant found')

        new_event = {
            "session_id":self._events_session_id,
            "computer_id":computer['id'],
            "type":computer['type'],
            "mode":computer['mode'],
            "variant_id": variant_id,
            "users_ids":[user['_id'] for user in users],
        }

        response = self._db[CollectionNames.EVENTS.value].insert_one(new_event)
        return {**new_event, "_id": str(response.inserted_id)}

    def __get_random_variant_id(self, type: int):
        if type == 1:
            response = self._db[CollectionNames.PR1_VARIANTS.value].aggregate([{ '$sample': { 'size': 1 } }])
        elif type == 2:
            response = self._db[CollectionNames.PR2_VARIANTS.value].aggregate([{ '$sample': { 'size': 1 } }])
        else:
            raise Exception(f"Not correct variant type. {type}")

        variants = [variant for variant in response]

        return str(variants[0]["_id"]) if variants else []

    def __emit_computer_event(self, computer, event_id, variant_id):
        variant = self._db[CollectionNames.PR1_VARIANTS.value].find_one({
            "_id": ObjectId(variant_id)
        })

        if computer['type'] == 1:
            all_bets = self.__get_all_bets()
            random_incoterms, incoterm_groups = self.__get_random_incoterm_groups()

            buyer_tables = []
            seller_tables = []
            for i, incoterms_group in enumerate(incoterm_groups):
                buyer_table = []
                seller_table = []
                for bet in all_bets:
                    buyer_dict = {}
                    seller_dict = {}

                    buyer_incoterms = bet['incoterms']["buyer"]
                    seller_incoterms = bet['incoterms']["seller"]

                    for incoterm in buyer_incoterms:
                        if incoterm in incoterms_group:
                            buyer_dict[incoterm] = bet["rate"]

                    for incoterm in seller_incoterms:
                        if incoterm in incoterms_group:
                            seller_dict[incoterm] = bet["rate"]

                    if buyer_dict:
                        buyer_table.append({'name': bet['name'], 'price': bet['rate'], **buyer_dict})
                    if seller_dict:
                        seller_table.append({'name': bet['name'], 'price': bet['rate'], **seller_dict})
                buyer_tables.append(buyer_table)
                seller_tables.append(seller_table)

            buyer_totals = []
            seller_totals = []

            for i in range(len(buyer_tables)):
                total = {incoterm: variant["product_price"] for incoterm in incoterm_groups[i]}
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
                    'legend': variant["legend"],
                    'product_price': variant["product_price"],
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
                    'test': variant["test"],
                    'random_incoterms': random_incoterms,
                    'all_bets': all_bets,
                },
            )

        if computer['type'] == 2:
            self._sio.emit(
                f'computer_{computer["id"]}_event',
                self.__practice_two(
                    variant_id=variant_id,
                    event_id=event_id,
                    computer_id=computer['id'],
                    event_mode=computer['mode'],
                    event_type=computer['type'],
                ),
            )

    def __practice_two(
        self, variant_id: str, event_id: int, computer_id: int, event_mode, event_type: int
    ):
        variant = self._db[CollectionNames.PR2_VARIANTS.value].find_one({"_id": ObjectId(variant_id)})
        points_codes = []

        for route in variant["routes"]:
            points_codes.extend([route["start_point_code"], route["transit_point_code"], route["end_point_code"]])
        points_codes = list(set(points_codes))

        points = self._db[CollectionNames.PR2_POINTS.value].find({
            "code": {"$in" : points_codes}
        })

        point_code_point_mapping = {str(point["code"]): point for point in points}

        for route in variant["routes"]:
            route["start_point_country"] = point_code_point_mapping[route["start_point_code"]]["country"]
            route["start_point_name"] = point_code_point_mapping[route["start_point_code"]]["name"]
            route["transit_point_country"] = point_code_point_mapping[route["transit_point_code"]]["country"]
            route["transit_point_name"] = point_code_point_mapping[route["transit_point_code"]]["name"]
            route["end_point_country"] = point_code_point_mapping[route["end_point_code"]]["country"]
            route["end_point_name"] = point_code_point_mapping[route["end_point_code"]]["name"]

        unique_routes_by_to_and_from_fields = []
        unique_pairs = set()

        for route in variant["routes"]:
            pair = (route['start_point_code'], route['end_point_code'])
            if pair not in unique_pairs:
                unique_pairs.add(pair)
                unique_routes_by_to_and_from_fields.append(route)

        containers_two_description = '\n'.join(
            [f'{route["start_point_country"]} - {route["end_point_country"]} {route["tons"]} т/месяц' for route in unique_routes_by_to_and_from_fields]
        )

        containers_two_description = (
            f'На основании изучения рынка и заключённых договоров на поставку продукции '
            f'сформированы {len(unique_routes_by_to_and_from_fields)} новых цепей поставок '
            f'продукции ежемесячно при разных условиях Инкотермс:\n' + containers_two_description
        )

        for route in unique_routes_by_to_and_from_fields:
            tons = route['tons']
            package_tons = variant["package_tons"]
            route['forty_containers_count'] = f'{tons}/(40*{package_tons})={int(tons / 40 * package_tons)}'
            route['route'] = f'{route["start_point_country"]} - {route["end_point_country"]}'

        containers = self._db[CollectionNames.PR2_CONTAINERS.value].find()

        container_first_table = []

        for c in containers:
            package_tons = variant["package_tons"]
            size = c['size']
            length = c['length']
            width = c['width']
            height = c['height']
            payload_capacity = c['payload_capacity']
            loading_volume = length * width * height
            package_length = variant["package_length"]
            package_width = variant["package_width"]
            package_height = variant["package_height"]
            transport_package_volume = package_length * package_width * package_height
            packages_in_container = math.ceil(
                math.floor(length / package_length)
                * math.floor(width / package_width)
                * math.floor(height / package_height)
            )

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
                'route': f'{route["start_point_country"]} - {route["end_point_country"]}',
                'destination_route': f'{route["start_point_country"]} - {route["end_point_country"]} через {route["transit_point_country"]}',
                'full_route': ' - '.join(
                    point_code_point_mapping[point_code]["name"]
                    for point_code in route['right_path']
                ),
            }
            for route in variant["routes"]
        ]

        bets_days_risks = []
        countries_route_dict = {}

        for route in variant["routes"]:
            answer = route["right_path"]

            days = 0

            for i in range(len(answer) - 1):
                route_info = self._db[CollectionNames.PR2_ROUTES.value].find_one({
                    "from_point_code": answer[i],
                    "to_point_code": answer[i+1]
                })

                days += route_info["days"]

            third_party_bets = [
                route.get('3PL1', None),
                route.get('3PL2', None),
                route.get('3PL3', None),
            ]

            third_party_bets = [bet for bet in third_party_bets if bet]

            points_types = {'ALL'}
            for point_code in answer:
                point = point_code_point_mapping[point_code]
                points_types.add(point["type"])

            all_risks = self._db[CollectionNames.PR2_RISKS.value].find()
            risks_answer = [risk['name'] for risk in all_risks if risk['type'] in points_types]
            all_risks = [risk['name'] for risk in all_risks]

            bets_days_risks.append(
                {
                    'full_route': ' - '.join(
                        point_code_point_mapping[point_code]["name"]
                        for point_code in route['right_path']
                    ),
                    'days': {'answer': days, 'all_options': self.__get_random_days_options(days)},
                    'bets': {
                        'answer': third_party_bets,
                        'all_options': self.__get_random_bets_options(third_party_bets),
                    },
                    'risks': {'answer': risks_answer, 'all_options': all_risks},
                }
            )

            route_number = 1
            country_route_name_count = {}

            for route in variant["routes"]:
                route_name = f"{route['start_point_country']} - {route['end_point_country']}"
                if route_name not in country_route_name_count:
                    country_route_name_count[route_name] = [{}, {}, {}]

                PL1, PL2, PL3 = route["bets"]
                containers_num = math.ceil(route['tons'] / (40 * route['package_tons']))

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
                    f"{route['start_point_country']} - {route['end_point_country']} через {route['transit_point_country']} " + PLS[0]['full_route_name']
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
            'routes': variant["routes"],
            'containers_one': container_first_table,
            'containers_two': {'description': containers_two_description, 'rows': unique_routes_by_to_and_from_fields,},
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
        all_incoterms = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "DPU", "DAP", "CPT", "CIP", "DDP"]
        incoterms = random.sample(all_incoterms, 9)
        incoterm_groups = [incoterms[i : i + 3] for i in range(0, len(incoterms), 3)]
        return incoterms, incoterm_groups

    def __get_all_bets(self):
        bets = self._db[CollectionNames.PR1_BETS.value].find()
        return [{**bet, "_id": str(bet["_id"])} for bet in bets]

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
