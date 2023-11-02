import math
from typing import List, Type, Optional
import random
import json

from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func
from sqlalchemy import desc

import models
import schemas
from services.service_collector import ServiceCollector


class EventService:
    def __init__(self, db_session: DBSession):
        self._db_session = db_session
        self._point_by_point_id_mapping = self._get_point_by_id_mapping()
        self._practice_one_steps_mapping = self._get_practice_one_steps_mapping()

    async def finish(self, event: models.Event):
        event.is_finished = True
        self._db_session.commit()

    async def get_current_step(self, event: models.Event):
        is_last_step = self.is_last_checkpoint(event)

        if is_last_step:
            return "results"

        curr_step_id = await self.get_last_step_id(event) + 1

        curr_step = self._db_session.query(models.PracticeOneStep if event.type == 1 else models.PracticeTwoStep).filter(
            (models.PracticeOneStep.id if event.type == 1 else models.PracticeTwoStep.id) == curr_step_id
        )

        if not curr_step:
            raise Exception("Not curr_step found")

        return {"step_id": curr_step.id, "step_name": curr_step.name}

    async def get_results(self, event: models.Event, users: List[models.User]):
        max_step_id = self._db_session.query(models.PracticeOneStep if event.type == 1 else models.PracticeTwoStep).count()
        results = []
        for user in users:
            result = (
                self._db_session.query(func.sum(models.EventCheckpoint.points), func.sum(models.EventCheckpoint.fails))
                .filter(models.EventCheckpoint.event_id == event.id, models.EventCheckpoint.user_id == user.id,)
                .first()
            )
            results.append({**user.to_json(), "points": result[0], "fails": result[1], "steps": max_step_id})
        return results

    async def create_checkpoints(
            self, event: models.Event, checkpoint_dto: schemas.CheckpointData, users: List[models.User]
    ):
        step_id = await self.get_last_step_id(event) + 1
        # В ПР1 могут балы получают по ролям, в пр2 одинаково
        if event.type == 1 and len(users) > 1:
            if self._practice_one_steps_mapping[step_id].role == "BUYER":
                users = users[0]
            elif self._practice_one_steps_mapping[step_id].role == "seller":
                users = users[1]
        else:
            raise Exception(f"TYPE {event.type} was not found")
        for user in users:
            checkpoint = models.EventCheckpoint(
                event_id=event.id,
                user_id=user.id,
                step_id=step_id,
                points=checkpoint_dto.points,
                fails=checkpoint_dto.fails
            )
            self._db_session.add(checkpoint)
            self._db_session.commit()

    async def get_last_step_id(self, event: models.Event):
        step = self._db_session.query(models.EventCheckpoint).order_by(desc(models.EventCheckpoint.created_at)).filter(models.EventCheckpoint.event_id == event.id).first()
        return step.id if step else 0

    async def is_last_checkpoint(self, event: models.Event):
        max_step_id = self._db_session.query(models.PracticeOneStep if event.type == 1 else models.PracticeTwoStep).count()

        last_step_id = await self.get_last_step_id(event)

        return max_step_id == last_step_id

    def create_events_session(self):
        events_session = models.Session()
        self._db_session.add(events_session)
        self._db_session.commit()
        return events_session

    def create_event(self, event: schemas.StartEventComputer, users: List[models.User], events_session:models.Session):
        variant = self._get_random_variant(event.type)

        if not variant:
            raise Exception('No random variant found')

        new_event = models.Event(
            session_id=events_session.id,
            computer_id=event.computer_id,
            type=event.type,
            mode=event.mode,
            variant_one_id=variant.id if event.type == 1 else None,
            variant_two_id=variant.id if event.type == 2 else None,
            user_1_id=users[0].id,
            user_2_id=users[1].id if len(users) > 1 else None,
        )
        self._db_session.add(new_event)
        self._db_session.commit()

        return new_event

    async def get_current_event_by_computer_id(self, services: ServiceCollector, computer_id: int):
        events_session_id = await services.redis.get_events_session_id()

        event: models.Event = await services.event.get_by_computer_and_session_ids(
            computer_id=computer_id, session_id=events_session_id
        )

        if not event:
            raise Exception("Event was not found!")

        return event

    def get_by_computer_and_session_ids(self, computer_id: int, session_id: int) -> Optional[Type[models.Event]]:
        event = self._db_session.query(models.Event).filter(
            models.Event.computer_id == computer_id, models.Event.session_id == session_id
        ).first()

        return event

    def get_variant_by_event(self, event: models.Event):
        variant = self._get_practice_one_variant(event) if event.type == 1 else self._get_practice_two_variant(event)
        return variant

    def _get_random_variant(self, type: int):
        return self._db_session.query(models.PracticeOneVariant if type == 1 else models.PracticeTwoVariant).order_by(func.random()).first()

    def __get_random_incoterm_groups(self):
        """Returns chosen incoterms and 3 incoterm groups divided by 3"""
        incoterms = [incoterm.value for incoterm in random.sample(list(models.Incoterms), 9)]

        incoterm_groups = [incoterms[i : i + 3] for i in range(0, len(incoterms), 3)]

        return incoterms, incoterm_groups

    def _get_practice_one_steps_mapping(self):
        steps = self._db_session.query(models.PracticeOneStep).all()
        return {step.id: step for step in steps}

    def _get_practice_one_variant(self, event: models.Event):
        all_bets = self._db_session.query(models.Bet).all()
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
            total = {incoterm: event.variant.product_price for incoterm in incoterm_groups[i]}
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

        return {
            'event_id': event.id,
            'type': event.type,
            'legend': event.variant.legend,
            'product_price': event.variant.product_price,
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
            'test': event.variant.test.to_json(),
            'random_incoterms': random_incoterms,
            'all_bets': models.Bet.to_json_list(all_bets),
        }

    def _get_point_by_id_mapping(self):
        points = self._db_session.query(models.Point).all()
        mapping = {point.id: point for point in points}
        return mapping

    def _get_routes_table(self, bets: List[models.PracticeTwoVariantBet]):
        routes_table = []

        for bet in bets:
            answer = json.loads(bet.answer)
            routes_table.append({
                "supply_chain": f"{bet.from_point.country} - {bet.to_point.country}",
                "route": f"{bet.from_point.country} - {bet.to_point.country} через {bet.transit_point.country}",
                "route_by_points": " - ".join([self._point_by_point_id_mapping[point_id].name for point_id in answer]),
                "route_by_points_ids": answer,
                "transit_contries": "ASK MAKS"
            })

        return routes_table

    def _get_days(self, bet: models.PracticeTwoVariantBet):
        correct_day = 0
        for i in range(len(bet.answer_array)-1):
            route = self._db_session.query(models.Route).filter(
                models.Route.from_point_id==bet.answer_array[i],
                models.Route.to_point_id==bet.answer_array[i+1]
            ).first()

            correct_day += route.days

        incorrect = self._get_random_days_options(correct_day)

        return [{"is_correct": True, "days": correct_day}, *incorrect]

    def _get_3PLS(self, bet: models.Bet):
        third_party_bets = [
                    bet.get('3PL1', None),
                    bet.get('3PL2', None),
                    bet.get('3PL3', None),
                ]

        correct = [{"is_correct": True, "num": PL} for PL in third_party_bets if PL]

        incorrect = self._get_random_3PLS_options(third_party_bets[0])

        return incorrect + correct

    def _get_risks(self, bet: models.PracticeTwoVariantBet, all_risks: List[models.Risk]):
        points_types = {'ALL'}
        for point_id in bet.answer_array:
            point = self._point_by_point_id_mapping[point_id]
            points_types.add(point.type)

        risks_answer = [{"is_correct": True, "name": risk.name} for risk in all_risks if risk.type in points_types]
        all_risks = [{"is_correct": False, "name": risk.name} for risk in all_risks if risk.type not in points_types]

        return {**all_risks, **risks_answer}

    def _get_risks_table(self, bets: List[models.PracticeTwoVariantBet]):
        risks_table = []
        all_risks = models.Risk.to_json_list(self._db_session.query(models.Risk).all())
        for bet in bets:
            days = self._get_days(bet)
            PLS = self._get_3PLS(bet)
            risks = self._get_risks(bet, all_risks)

            risks_table.append({
                "days": days,
                "3PLS": PLS,
                "risks": risks
            })

        return risks_table

    def _get_all_routes_calculations(self, bets: List[models.PracticeTwoVariantBet]):
        all_routes_calculations = {}
        route_number = 1

        for bet in bets:
            route_name = f"{bet.from_point.country} - {bet.to_point.country}"

            PL1, PL2, PL3 = bet.third_party_logistics_1, bet.third_party_logistics_2, bet.third_party_logistics_3
            containers_num = math.ceil(bet.tons / (40 * bet.variant.package_tons))

            PLS = []

            if PL1:
                PLS.append(
                    {
                        'full_route_name': '3PL1',
                        'route_number': route_number,
                        'bet': PL1,
                        'delivery_price': f'{PL1}*{containers_num}={PL1 * containers_num}',
                        'containers_num': containers_num
                    }
                )

                route_number += 1
            if PL2:
                PLS.append(
                    {
                        'full_route_name': '3PL2',
                        'route_number': route_number,
                        'bet': PL2,
                        'delivery_price': f'{PL2}*{containers_num}={PL2 * containers_num}',
                        'containers_num': containers_num
                    }
                )

                route_number += 1
            if PL3:
                PLS.append(
                    {
                        'full_route_name': '3PL3',
                        'route_number': route_number,
                        'bet': PL3,
                        'delivery_price': f'{PL3}*{containers_num}={PL3 * containers_num}',
                        'containers_num': containers_num
                    }
                )

                route_number += 1

            PLS[0]['full_route_name'] = (
                    f"{bet.from_point.country} - {bet.to_point.country} через {bet.transit_point.country} " + PLS[0]['full_route_name']
            )

            PLS = [PL for PL in PLS if PL]

            if route_name not in all_routes_calculations:
                all_routes_calculations[route_name] = PLS
            else:
                all_routes_calculations[route_name].extend(PLS)

        return all_routes_calculations

    def _get_practice_two_variant(self, event: models.Event):
        bets = models.PracticeTwoVariantBet.to_json_list(event.variant.bets)

        introduction_table = self._get_introduction_table(bets)
        first_containers_table = self._get_first_containers_table(event)
        second_containers_table = self._get_second_containers_table(event, bets)
        routes = self._get_routes_table(bets)
        risks_table = self._get_risks_table(bets)
        all_routes_calculations = self._get_all_routes_calculations(bets)
        overall = self._overall_calculations(all_routes_calculations=all_routes_calculations)

        return {
            'event_id': event.id,
            'mode': event.mode,
            'type': event.type,
            'legend': event.variant.legend,
            'introduction_table': introduction_table,
            'containers_one_table': first_containers_table,
            'containers_two_table': second_containers_table,
            'routes_table': routes,
            'risks_table': risks_table,
            'all_routes_calculations': all_routes_calculations,
            'overall_calculations': overall,
        }

    def _get_second_containers_table(self, event: models.Event, bets: List[models.PracticeTwoVariantBet]):
        unique_bets_by_to_and_from_fields = []
        unique_pairs = set()

        for bet in bets:
            pair = (bet.from_point, bet.to_point)
            if pair not in unique_pairs:
                unique_pairs.add(pair)
                unique_bets_by_to_and_from_fields.append(bet)

        bets_description = '\n'.join(
            [f'{bet.from_point.country} - {bet.to_point.country} {bet.tons} т/месяц' for bet in unique_bets_by_to_and_from_fields]
        )

        description = (
                f'На основании изучения рынка и заключённых договоров на поставку продукции '
                f'сформированы {len(unique_bets_by_to_and_from_fields)} новых цепей поставок '
                f'продукции ежемесячно при разных условиях Инкотермс:\n' + bets_description
        )

        rows = []
        for bet in unique_bets_by_to_and_from_fields:
            package_tons = event.variant.package_tons
            rows.append({
                "supply_chain": f"{bet.from_point.country} - {bet.to_point.country}",
                "tons": bet.tons,
                "containers_quantity": f'{bet.tons}/(40*{package_tons})={int(bet.tons / 40 * package_tons)}'

            })

        return {"description": description, "rows": rows}

    def _get_introduction_table(self, bets: List[models.PracticeTwoVariantBet]):
        # Первый скрин с табличкой
        introduction_table = []

        for bet in bets:
            introduction_table.append({
                "purpose_of_supply": f"{bet.from_point.country} - {bet.to_point.country}",
                "delivery_route": f"{bet.from_point.country} - {bet.to_point.country} через {bet.transit_point.country}",
                "3PL1": bet.third_party_logistics_1,
                "3PL2": bet.third_party_logistics_2,
                "3PL3": bet.third_party_logistics_3
            })

        return introduction_table

    def _get_first_containers_table(self, event: models.Event):
        first_containers_table = []

        containers = models.Container.to_json_list(self._db_session.query(models.Container).all())

        for c in containers:
            length = c['length']
            width = c['width']
            height = c['height']
            loading_volume = length * width * height
            package_length = event.variant.package_length
            package_width = event.variant.package_width
            package_height = event.variant.package_height
            transport_package_volume = package_length * package_width * package_height
            packages_in_container = math.ceil(
                math.floor(length / package_length)
                * math.floor(width / package_width)
                * math.floor(height / package_height)
            )
            size = c['size']
            payload_capacity = c['payload_capacity']

            first_containers_table.append(
                {
                    'type': f'{size}-футовый контейнер {length}м*{width}м*{height}м (Д*Ш*В), грузоподъёмность {payload_capacity}т',
                    'loading_volume': f'{length}*{width}*{height}={self.f(loading_volume)}',
                    'transport_package_volume': f'{package_length}*{package_width}*{package_height}={self.f(transport_package_volume)}',
                    'packages_in_container': f'({length}/{package_length})*({width}/{package_width})*({height}/{package_height})={packages_in_container}',
                    'capacity_utilization_rate': f'{self.f(packages_in_container)}*{self.f(transport_package_volume)}/{self.f(loading_volume)}={self.f(packages_in_container * transport_package_volume / loading_volume)}',
                    'payload_utilization_rate': f'{packages_in_container}*{event.variantpackage_tons}/{payload_capacity}={self.f(packages_in_container * event.variant.package_tons / payload_capacity)}',
                }
            )

        return first_containers_table

    def _find_option(self, PL_name, variant_num, all_routes_calculations):
        stack = []
        for val in all_routes_calculations.values():
            index = 0
            for dic in val:
                pl_options = [dic for dic in val if PL_name in dic['full_route_name']]
                if PL_name in dic['full_route_name']:
                    if variant_num == 2:
                        if dic.get('full_route_name') == pl_options[1].get('full_route_name'):
                            stack.append({
                                "delivery_price": dic.get('delivery_price') * dic.get('containers_num', 1),
                                "route_number": index
                            })
                    else:
                        stack.append({
                            "delivery_price": dic.get('delivery_price') * dic.get('containers_num', 1),
                            "route_number": index
                        })
                index += 1

        total = self.f(sum(route['delivery_price'] for route in stack) / 1000)
        route_numbers = [str(route['route_number']) for route in stack]

        return f"{total}: {'-'.join(route_numbers)}"

    def _find_optimal_option(self, all_routes_calculations, variant_num):
        # [{
        #                         'full_route_name': '3PL1',
        #                         'route_number': route_number,
        #                         'bet': PL1,
        #                         'delivery_price': f'{PL1}*{containers_num}={PL1 * containers_num}',
        #                     }]
        stack = []
        for val in all_routes_calculations.values():
            all_nums = [{"delivery_price": dic['delivery_price'], "route_number": dic['route_number']} for dic in val]
            all_nums.sort(key=lambda dic: dic['delivery_price'])
            stack.append(all_nums[0 if variant_num == 1 else 1])

        total = self.f(sum(route['delivery_price'] for route in stack) / 1000)
        route_numbers = [str(route['route_number']) for route in stack]

        return f"{total}: {'-'.join(route_numbers)}"

    def _overall_calculations(self, all_routes_calculations):
        optimal_solution1 = self._find_optimal_option(all_routes_calculations=all_routes_calculations, variant_num=1)
        optimal_solution2 = self._find_optimal_option(all_routes_calculations=all_routes_calculations, variant_num=2)

        PL1_variant1 = self._find_option(PL_name='PL1', variant_num=1, all_routes_calculations=all_routes_calculations)
        PL1_variant2 = self._find_option(PL_name='PL1', variant_num=2, all_routes_calculations=all_routes_calculations)

        PL2_variant1 = self._find_option(PL_name='PL2', variant_num=1, all_routes_calculations=all_routes_calculations)
        PL2_variant2 = self._find_option(PL_name='PL2', variant_num=2, all_routes_calculations=all_routes_calculations)

        PL3_variant1 = self._find_option(PL_name='PL3', variant_num=1, all_routes_calculations=all_routes_calculations)
        PL3_variant2 = self._find_option(PL_name='PL3', variant_num=2, all_routes_calculations=all_routes_calculations)

        return {
            '3PL1': {'first': PL1_variant1, 'second': PL1_variant2},
            '3PL2': {'first': PL2_variant1, 'second': PL2_variant2},
            '3PL3': {'first': PL3_variant1, 'second': PL3_variant2},
            'optimal': {'first': optimal_solution1, 'second': optimal_solution2},
        }

    @staticmethod
    def _get_random_days_options(days: int):
        s = {days}
        for _ in range(15):
            num = random.randint(days - 20, days + 30)
            if num > 1:
                s.add(num)
        s.remove(days)
        return [{"is_correct": False, "days": days} for days in s]

    @staticmethod
    def _get_random_3PLS_options(num: int):
        incorrect_3PLS = set()

        for _ in range(15):
            num = random.randint(int(num / 100 - 20), int(num / 100 + 40))
            if num > 5:
                incorrect_3PLS.add(num * 100)

        incorrect_3PLS = [{"is_correct": False, "num": PL} for PL in incorrect_3PLS]

        return incorrect_3PLS

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
