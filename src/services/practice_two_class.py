import copy
import datetime
import math
import random
from typing import (
    Optional,
    Type,
    Union,
)

from bson import ObjectId

from constants.pr2_class_info import pr2_class_info
from db.mongo import (
    CollectionNames,
    get_db,
)
from schemas import (
    BestPL,
    ButtonNumber,
    CheckpointData,
    CheckpointResponse,
    CheckpointResponseStatus,
    ContainerResult,
    ContainerRoute,
    CurrentStepResponse,
    EventInfo,
    EventStepResult,
    FormulaRow,
    FullRoute,
    FullRouteHint,
    MiniRoute,
    MiniRouteHint,
    PackageSize,
    PLOption,
    PLRoute,
    PR2ClassEvent,
    PR2ClassResult,
    PR2Point,
    PR2Risk,
    PR2SourceData,
    RisksWithRouteName,
    RoutePart,
    RouteWithRisk,
    StartEventDto,
    Step,
    UserHistoryElement,
    UserOut,
)
from services.utils import normalize_mongo


class PracticeTwoClass:
    def __init__(self, users_ids: list[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    @staticmethod
    def _get_next_code_by_id(index):
        return pr2_class_info.steps_codes[index]

    @staticmethod
    def handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step):
        last_step_result = event.steps_results[-1]
        is_last_attempt = event.current_step.code == last_step_result.step_code and last_step_result.fails == 2

        if event.current_step.code != last_step_result.step_code:
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0)
            )

        if is_last_attempt or not is_failed:
            event.current_step = next_step
            checkpoint_response.next_step = next_step

        if is_failed:
            event.steps_results[-1].fails += 1
            checkpoint_response.status = (
                CheckpointResponseStatus.FAILED.value if is_last_attempt else CheckpointResponseStatus.TRY_AGAIN.value
            )
        else:
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

        checkpoint_response.fails = event.steps_results[-1].fails

    def get_results(self, event: PR2ClassEvent) -> list[PR2ClassResult]:
        pr2_class_results = []

        for user_id in event.users_ids:
            user_db = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user_id)})

            step_codes_with_point_system = [
                'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER',
                'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
                'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY',
                'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER',
                'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
                'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY',
                'SCREEN_8_MAP_ROUTE_1',
                'SCREEN_8_MAP_ROUTE_2',
                'SCREEN_8_MAP_ROUTE_3',
                'SCREEN_8_MAP_ROUTE_4',
                'SCREEN_8_MAP_ROUTE_5',
                'SCREEN_8_MAP_ROUTE_6',
                'SCREEN_8_MAP_ROUTE_7',
                'SCREEN_8_MAP_ROUTE_8',
            ]

            errors = 0
            points = 0

            for step_result in event.steps_results:
                if step_result.step_code in step_codes_with_point_system:
                    if step_result.fails == 3:
                        errors += 1
                    elif step_result.fails == 0:
                        points += 3
                    elif step_result.fails == 1:
                        points += 2
                    elif step_result.fails == 2:
                        points += 1

            user = normalize_mongo(user_db, UserOut)

            pr2_class_results.append(
                PR2ClassResult(
                    name=user.first_name,
                    last_name=user.last_name,
                    surname=user.surname,
                    group_name=user.group_name,
                    errors=errors,
                    points=points,
                )
            )

        return pr2_class_results

    def checkpoint(self, event: Union[PR2ClassEvent, Type[PR2ClassEvent]], checkpoint_dto: CheckpointData):
        checkpoint_response = CheckpointResponse()

        if checkpoint_dto.step_code != event.current_step.code:
            raise Exception(f'Backend ждёт {event.current_step.code} step_code')

        if checkpoint_dto.step_code == 'SCREEN_1_INSTRUCTION_WITH_LEGEND':
            next_step = Step(id=1, code=self._get_next_code_by_id(1),)
            checkpoint_response.next_step = next_step
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0,)
            )
            event.current_step = next_step

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Тут ошибиться невозможно. Просто скипается'

        if checkpoint_dto.step_code == 'SCREEN_2_TASK_DESCRIPTION':
            next_step = Step(id=2, code=self._get_next_code_by_id(2),)
            checkpoint_response.next_step = next_step
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0,)
            )
            event.current_step = next_step

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Тут ошибиться невозможно. Просто скипается'

        if checkpoint_dto.step_code == 'SCREEN_3_SOURCE_DATA_FULL_ROUTES':
            next_step = Step(id=3, code=self._get_next_code_by_id(3))

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Тут ошибиться невозможно. Просто скипается'

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME':
            next_step = Step(id=4, code=self._get_next_code_by_id(4))

            is_failed = checkpoint_dto.formula not in [
                '5.9*2.35*2.33',
                '5.9*2.33*2.35',
                '2.33*5.9*2.35',
                '2.33*2.35*5.9',
                '2.35*5.9*2.33',
                '2.35*2.33*5.9',
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = """
            Заполняем поле formula
            
            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих:
            ['5.9*2.35*2.33','5.9*2.33*2.35','2.33*5.9*2.35','2.33*2.35*5.9','2.35*5.9*2.33','2.35*2.33*5.9']
            """

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME':
            next_step = Step(id=5, code=self._get_next_code_by_id(5),)

            right_formulas = [
                f'{event.source_data.package_size.length:g}*{event.source_data.package_size.width:g}*{event.source_data.package_size.height:g}',
                f'{event.source_data.package_size.length:g}*{event.source_data.package_size.height:g}*{event.source_data.package_size.width:g}',
                f'{event.source_data.package_size.height:g}*{event.source_data.package_size.width:g}*{event.source_data.package_size.length:g}',
                f'{event.source_data.package_size.height:g}*{event.source_data.package_size.length:g}*{event.source_data.package_size.width:g}',
                f'{event.source_data.package_size.width:g}*{event.source_data.package_size.height:g}*{event.source_data.package_size.length:g}',
                f'{event.source_data.package_size.width:g}*{event.source_data.package_size.length:g}*{event.source_data.package_size.height:g}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER':
            next_step = Step(id=6, code=self._get_next_code_by_id(6),)

            right_formulas = [
                f'5.9/{event.source_data.package_size.length:g}*(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})',
                f'(5.9/{event.source_data.package_size.length:g})*(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})',
                f'5.9/{event.source_data.package_size.length:g}*(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})',
                f'(5.9/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})',
                f'2.35/{event.source_data.package_size.height:g}*(2.33/{event.source_data.package_size.width:g})*(5.9/{event.source_data.package_size.length:g})',
                f'(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})*(5.9/{event.source_data.package_size.length:g})',
                f'2.35/{event.source_data.package_size.height:g}*(5.9/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.width:g})',
                f'(2.35/{event.source_data.package_size.height:g})*(5.9/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.width:g})',
                f'2.33/{event.source_data.package_size.width:g}*(2.35/{event.source_data.package_size.height:g})*(5.9/{event.source_data.package_size.length:g})',
                f'(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})*(5.9/{event.source_data.package_size.length:g})',
                f'2.33/{event.source_data.package_size.width:g}*(5.9/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})',
                f'(2.33/{event.source_data.package_size.width:g})*(5.9/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION':
            next_step = Step(id=7, code=self._get_next_code_by_id(7),)

            right_formulas = [
                f'{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.transport_package_volume:g}/{event.source_data.loading_volume_20_foot_container:g}',
                f'{event.source_data.transport_package_volume:g}*{event.source_data.number_of_packages_in_20_foot_container}/{event.source_data.loading_volume_20_foot_container:g}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY':
            next_step = Step(id=8, code=self._get_next_code_by_id(8),)

            right_formulas = [
                f'{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton:g}/21.8',
                f'{event.source_data.package_weight_in_ton:g}/21.8*{event.source_data.number_of_packages_in_20_foot_container}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME':
            next_step = Step(id=9, code=self._get_next_code_by_id(9),)

            right_formulas = [
                '12*2.33*2.35',
                '12*2.35*2.33',
                '2.33*12*2.35',
                '2.33*2.35*12',
                '2.35*12*2.33',
                '2.35*2.33*12',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME':
            next_step = Step(id=10, code=self._get_next_code_by_id(10),)

            right_formulas = [
                f'{event.source_data.package_size.length:g}*{event.source_data.package_size.width:g}*{event.source_data.package_size.height:g}',
                f'{event.source_data.package_size.length:g}*{event.source_data.package_size.height:g}*{event.source_data.package_size.width:g}',
                f'{event.source_data.package_size.height:g}*{event.source_data.package_size.width:g}*{event.source_data.package_size.length:g}',
                f'{event.source_data.package_size.height:g}*{event.source_data.package_size.length:g}*{event.source_data.package_size.width:g}',
                f'{event.source_data.package_size.width:g}*{event.source_data.package_size.height:g}*{event.source_data.package_size.length:g}',
                f'{event.source_data.package_size.width:g}*{event.source_data.package_size.length:g}*{event.source_data.package_size.height:g}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER':
            next_step = Step(id=11, code=self._get_next_code_by_id(11),)

            right_formulas = [
                f'12/{event.source_data.package_size.length:g}*(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})',
                f'(12/{event.source_data.package_size.length:g})*(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})',
                f'12/{event.source_data.package_size.length:g}*(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})',
                f'(12/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})',
                f'2.35/{event.source_data.package_size.height:g}*(2.33/{event.source_data.package_size.width:g})*(12/{event.source_data.package_size.length:g})',
                f'(2.35/{event.source_data.package_size.height:g})*(2.33/{event.source_data.package_size.width:g})*(12/{event.source_data.package_size.length:g})',
                f'2.35/{event.source_data.package_size.height:g}*(12/{event.source_data.package_size.length:g})*(2.33/{event.source_data.package_size.width:g})',
                f'(2.35/{event.source_data.package_size.height:g})*(12/{event.source_data.package_size.length:g})*(2.33/{event.source_data.package_size.width:g})',
                f'2.33/{event.source_data.package_size.width:g}*(2.35/{event.source_data.package_size.height:g})*(12/{event.source_data.package_size.length:g})',
                f'(2.33/{event.source_data.package_size.width:g})*(2.35/{event.source_data.package_size.height:g})*(12/{event.source_data.package_size.length:g})',
                f'2.33/{event.source_data.package_size.width:g}*(12/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})',
                f'(2.33/{event.source_data.package_size.width:g})*(12/{event.source_data.package_size.length:g})*(2.35/{event.source_data.package_size.height:g})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION':
            next_step = Step(id=12, code=self._get_next_code_by_id(12),)

            right_formulas = [
                f'{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.transport_package_volume:g}/{event.source_data.loading_volume_40_foot_container:g}',
                f'{event.source_data.transport_package_volume:g}*{event.source_data.number_of_packages_in_40_foot_container}/{event.source_data.loading_volume_40_foot_container:g}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY':
            next_step = Step(id=13, code=self._get_next_code_by_id(13),)

            right_formulas = [
                f'{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g}/21.8',
                f'{event.source_data.package_weight_in_ton:g}/21.8*{event.source_data.number_of_packages_in_40_foot_container}',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula

            Проверяем, что checkpoint_dto.formula = какому-либо значению из этих: {right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_5_DESCRIBE_CONTAINER_SELECTION':
            next_step = Step(id=14, code=self._get_next_code_by_id(14),)

            event.container_selection_explanation = checkpoint_dto.text

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле text
            """

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_1':
            next_step = Step(id=15, code=self._get_next_code_by_id(15),)

            right_formulas = [
                f'{event.source_data.mini_routes[0].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{event.source_data.mini_routes[0].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            right_formulas={right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_2':
            next_step = Step(id=16, code=self._get_next_code_by_id(16),)

            right_formulas = [
                f'{event.source_data.mini_routes[1].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{event.source_data.mini_routes[1].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            right_formulas={right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_3':
            next_step = Step(id=17, code=self._get_next_code_by_id(17),)

            right_formulas = [
                f'{event.source_data.mini_routes[2].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{event.source_data.mini_routes[2].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            right_formulas={right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_4':
            next_step = Step(id=18, code=self._get_next_code_by_id(18),)

            right_formulas = [
                f'{event.source_data.mini_routes[3].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{event.source_data.mini_routes[3].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            right_formulas={right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_5':
            next_step = Step(id=19, code=self._get_next_code_by_id(19),)

            right_formulas = [
                f'{event.source_data.mini_routes[4].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{event.source_data.mini_routes[4].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ]

            is_failed = checkpoint_dto.formula not in right_formulas

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Заполняем поле formula
            
            right_formulas={right_formulas}
            """

        if checkpoint_dto.step_code == 'SCREEN_7_SOURCE_DATA_CHOOSE_DESTINATIONS':
            next_step = Step(id=20, code=self._get_next_code_by_id(20),)

            checkpoint_response.hint = (
                'Нужно заполнить поле: destination_points_codes ( лист из кодов правильных точек )'
            )

            right_destination_points_codes = {
                event.source_data.full_routes[0].points[-1].code,
                event.source_data.full_routes[4].points[-1].code,
                event.source_data.full_routes[5].points[-1].code,
                event.source_data.full_routes[6].points[-1].code,
                event.source_data.full_routes[7].points[-1].code,
            }

            is_failed = right_destination_points_codes != set(checkpoint_dto.destination_points_codes)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_7_SOURCE_DATA_CHOOSE_PORTS':
            next_step = Step(id=21, code=self._get_next_code_by_id(21),)

            checkpoint_response.hint = 'Нужно заполнить поле: ports_codes ( лист из кодов правильных точек )'

            right_ports_codes = set()
            for r in event.source_data.full_routes:
                for p in r.points:
                    if p.type == 'PORT':
                        right_ports_codes.add(p.code)

            is_failed = checkpoint_dto.ports_codes is None or right_ports_codes != set(checkpoint_dto.ports_codes)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_7_SOURCE_DATA_CHOOSE_BORDER':
            next_step = Step(id=22, code=self._get_next_code_by_id(22),)

            right_borders_codes = set()
            for r in event.source_data.full_routes:
                for p in r.points:
                    if p.type == 'BORDER':
                        right_borders_codes.add(p.code)

            is_failed = checkpoint_dto.borders_codes is None or right_borders_codes != set(checkpoint_dto.borders_codes)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            checkpoint_response.hint = f"""
            Нужно заполнить поле: borders_codes
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_1':
            next_step = Step(id=23, code=self._get_next_code_by_id(23),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[0].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[0].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_2':
            next_step = Step(id=24, code=self._get_next_code_by_id(24),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[1].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[1].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_3':
            next_step = Step(id=25, code=self._get_next_code_by_id(25),)

            codes = [p.code for p in event.source_data.full_routes[2].points]
            option1 = []
            option2 = []

            for point_code in codes:
                if point_code in ['UZBEKISTAN_ALTUNKUL_BORDER', 'KAZAKHSTAN_DOSTIK_BORDER']:
                    option1.append('UZBEKISTAN_ALTUNKUL_BORDER')
                    option2.append('KAZAKHSTAN_DOSTIK_BORDER')
                else:
                    option1.append(point_code)
                    option2.append(point_code)

            is_failed = checkpoint_dto.route_points_codes != option1 and checkpoint_dto.route_points_codes != option2
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[2].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_4':
            next_step = Step(id=26, code=self._get_next_code_by_id(26),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[3].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[3].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_5':
            next_step = Step(id=27, code=self._get_next_code_by_id(27),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[4].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[4].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_6':
            next_step = Step(id=28, code=self._get_next_code_by_id(28),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[5].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[5].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_7':
            next_step = Step(id=29, code=self._get_next_code_by_id(29),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[6].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[6].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_8':
            next_step = Step(id=30, code=self._get_next_code_by_id(30),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[7].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f"""
            Тут нужно заполнить поле route_points_codes. Это массив из кодов точке list[str]
            
            Правильный ответ: {[p.code for p in event.source_data.full_routes[7].points]}
            """

        if checkpoint_dto.step_code == 'SCREEN_9_FORMED_ROUTES_TABLE':
            next_step = Step(id=31, code=self._get_next_code_by_id(31),)
            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Скипаем, инфо скрин'

        if checkpoint_dto.step_code == 'SCREEN_10_RISKS_1':
            next_step = Step(id=32, code=self._get_next_code_by_id(32),)
            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

            risks_mapping = {risk.id: risk for risk in pr2_class_info.all_risks[0]}

            checkpoint_response.hint = f'заполняем risk_codes_desc'

            event.risks_chosen_by_user.append(
                RisksWithRouteName(
                    route_name='МАРШРУТ ЧЕРЕЗ РОССИЮ (ЧЕРЕЗ ЗАБАЙКАЛЬСК И БРЕСТ)',
                    risks=[risks_mapping[id] for id in checkpoint_dto.risk_ids_desc],
                )
            )

        if checkpoint_dto.step_code == 'SCREEN_10_RISKS_2':
            next_step = Step(id=33, code=self._get_next_code_by_id(33),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'заполняем risk_codes_desc'

            risks_mapping = {risk.id: risk for risk in pr2_class_info.all_risks[1]}

            event.risks_chosen_by_user.append(
                RisksWithRouteName(
                    route_name='МАРШРУТ ЧЕРЕЗ РОССИЮ (ЧЕРЕЗ ЗАБАЙКАЛЬСК И БРЕСТ)',
                    risks=[risks_mapping[id] for id in checkpoint_dto.risk_ids_desc],
                )
            )

        if checkpoint_dto.step_code == 'SCREEN_10_RISKS_3':
            next_step = Step(id=34, code=self._get_next_code_by_id(34),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'заполняем risk_codes_desc'

            risks_mapping = {risk.id: risk for risk in pr2_class_info.all_risks[2]}

            event.risks_chosen_by_user.append(
                RisksWithRouteName(
                    route_name='МАРШРУТ ЧЕРЕЗ РОССИЮ (ЧЕРЕЗ ЗАБАЙКАЛЬСК И БРЕСТ)',
                    risks=[risks_mapping[id] for id in checkpoint_dto.risk_ids_desc],
                )
            )

        if checkpoint_dto.step_code == 'SCREEN_10_RISKS_4':
            next_step = Step(id=35, code=self._get_next_code_by_id(35),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'заполняем risk_codes_desc'

            risks_mapping = {risk.id: risk for risk in pr2_class_info.all_risks[3]}

            event.risks_chosen_by_user.append(
                RisksWithRouteName(
                    route_name='МАРШРУТ ЧЕРЕЗ РОССИЮ (ЧЕРЕЗ ЗАБАЙКАЛЬСК И БРЕСТ)',
                    risks=[risks_mapping[id] for id in checkpoint_dto.risk_ids_desc],
                )
            )

        if checkpoint_dto.step_code == 'SCREEN_10_RISKS_TOTAL':
            next_step = Step(id=36, code=self._get_next_code_by_id(36),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'Уверенный скип'

        if checkpoint_dto.step_code == 'SCREEN_10_FULL_ROUTES_WITH_PLS':
            next_step = Step(id=37, code=self._get_next_code_by_id(37),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Тут просили сразу ошибку в ячейке показывать, а баллы за это все не ставим. Предлагаю на фронте обрабатывать, чтобы не делать 42 доп чекпоинта'

        if checkpoint_dto.step_code == 'SCREEN_11_OPTIMAL_RESULTS_3PL1':
            next_step = Step(id=38, code=self._get_next_code_by_id(38),)

            answer_ids = [r.best_pls[0].index for r in event.source_data.mini_routes]

            is_failed = set(checkpoint_dto.answer_ids) != set(answer_ids)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'Правильные индексы (answer_ids)=: f{answer_ids}'

        if checkpoint_dto.step_code == 'SCREEN_11_OPTIMAL_RESULTS_3PL2':
            next_step = Step(id=39, code=self._get_next_code_by_id(39),)

            answer_ids = [r.best_pls[1].index for r in event.source_data.mini_routes]

            is_failed = set(checkpoint_dto.answer_ids) != set(answer_ids)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'Правильные индексы (answer_ids)=: f{answer_ids}'

        if checkpoint_dto.step_code == 'SCREEN_11_OPTIMAL_RESULTS_3PL3':
            next_step = Step(id=40, code=self._get_next_code_by_id(40),)

            answer_ids = [r.best_pls[2].index for r in event.source_data.mini_routes]

            is_failed = set(checkpoint_dto.answer_ids) != set(answer_ids)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'Правильные индексы (answer_ids)=: f{answer_ids}'

        if checkpoint_dto.step_code == 'SCREEN_11_OPTIMAL_RESULTS_COMBO':
            next_step = Step(id=41, code=self._get_next_code_by_id(41),)

            answer_ids = [r.best_pls[3].index for r in event.source_data.mini_routes]

            is_failed = set(checkpoint_dto.answer_ids) != set(answer_ids)

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = f'Правильные индексы (answer_ids)=: f{answer_ids}'

        if checkpoint_dto.step_code == 'SCREEN_12_OPTIMAL_WITH_RISKS':
            next_step = Step(id=42, code=self._get_next_code_by_id(42),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)
            checkpoint_response.hint = 'Все уже заполнено за нас'

        if checkpoint_dto.step_code == 'SCREEN_13_CHOOSE_LOGIST':
            next_step = Step(id=-1, code='FINISH',)

            event.delivery_option_explanation = checkpoint_dto.text

            event.is_finished = True
            event.finished_at = datetime.datetime.now()
            event.results = self.get_results(event)

            for i, user_id in enumerate(event.users_ids):
                history_element = UserHistoryElement(
                    id=event.id,
                    type=event.event_type,
                    mode=event.event_mode,
                    created_at=event.created_at,
                    finished_at=event.finished_at,
                    errors=event.results[i].errors,
                    points=event.results[i].points,
                    container_selection_explanation=event.container_selection_explanation,
                    delivery_option_explanation=checkpoint_dto.text,
                    risks_chosen_by_user=event.risks_chosen_by_user,
                )

                self.db[CollectionNames.USERS.value].update_one(
                    {'_id': ObjectId(user_id)}, {'$push': {'history': history_element.dict()}}
                )

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        self.db[CollectionNames.EVENTS.value].update_one({'_id': ObjectId(event.id)}, {'$set': event.dict()})

        return checkpoint_response

    @staticmethod
    def _get_source_data_choose_destinations_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.all_points = event.source_data.all_points
        step_response.departure_points_strs = event.source_data.departure_points_strs

        return step_response

    @staticmethod
    def _get_source_data_choose_ports_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.all_points = event.source_data.all_points
        step_response.departure_points_strs = event.source_data.departure_points_strs
        step_response.destination_points_codes = event.source_data.destination_points_codes

        return step_response

    @staticmethod
    def _get_source_data_choose_border_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.all_points = event.source_data.all_points
        step_response.departure_points_strs = event.source_data.departure_points_strs
        step_response.destination_points_codes = event.source_data.destination_points_codes
        step_response.ports_points_codes = event.source_data.ports_points_codes
        step_response.borders_points_codes = event.source_data.borders_points_codes
        step_response.terminals_points_codes = event.source_data.terminals_points_codes

        return step_response

    def create(self, event_dto: StartEventDto):
        zero_step = Step(id=1, code=f'SCREEN_1_INSTRUCTION_WITH_LEGEND', name=f'Легенда и Инструкция',)

        all_destination_countries = ['Польша', 'Германия', 'Франция', 'Нидерланды', 'Бельгия', 'Чехия', 'Австрия']
        random.shuffle(all_destination_countries)
        random_destination_country_for_china = all_destination_countries[0]
        random_destination_countries_for_japan = all_destination_countries[1:3]
        random_destination_countries_for_south_korea = all_destination_countries[3:5]
        random_city_from_for_china = random.choice(['Шицзячжуан', 'Цзинань', 'Иу', 'Баодин'])
        random_city_from_for_japan = random.choice(['Киото', 'Аябе', 'Асаго', 'Мацумото'])
        random_city_from_for_south_korea = random.choice(['Сувон', 'Тэджон', 'Чханвон', 'Кванджу'])

        destination_cities_by_destination_country = {
            'Польша': ['Острава', 'Лодзь'],
            'Германия': ['Лейпциг', 'Аугсбург'],
            'Франция': ['Руан', 'Лион'],
            'Нидерланды': ['Утрехт', 'Харлем'],
            'Бельгия': ['Лёвен', 'Гент'],
            'Чехия': ['Пардубице', 'Пльзень'],
            'Австрия': ['Линц', 'Санкт-Пёльтен'],
        }

        random_destination_city_for_china = random.choice(
            destination_cities_by_destination_country[random_destination_country_for_china]
        )

        random_destination_cities_for_japan = [
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[0]]),
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[1]]),
        ]

        random_destination_cities_for_south_korea = [
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[0]]),
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[1]]),
        ]

        dynamic_borders = ['Достык', 'Алтынколь']
        chosen_dynamic_border = random.choice(dynamic_borders)

        random_china_port = random.choice(['Гуанчжоу', 'Нинбо', 'Чунцин', 'Циндао'])
        random_japan_port = random.choice(['Акита', 'Йокогама', 'Кобе', 'Нагоя'])
        random_south_korea_port = random.choice(['Пусан', 'Инчон'])
        random_russia_port = random.choice(['Владивосток', 'Восточный'])

        routes_tons = [
            random.randint(10, 16) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100,
        ]

        package_size = self.get_random_package_size()
        package_weight_in_ton = random.randint(1, 9) / 10

        n_of_transport_packages_in_container_20 = math.floor(
            math.floor(5.9 / package_size.length)
            * math.floor(2.33 / package_size.width)
            * math.floor(2.35 / package_size.height)
        )

        n_of_transport_packages_in_container_40 = math.floor(
            math.floor(12 / package_size.length)
            * math.floor(2.33 / package_size.width)
            * math.floor(2.35 / package_size.height)
        )

        full_routes = self.get_full_routes(
            random_destination_country_for_china=random_destination_country_for_china,
            random_city_from_for_china=random_city_from_for_china,
            random_destination_city_for_china=random_destination_city_for_china,
            chosen_dynamic_border=chosen_dynamic_border,
            random_destination_countries_for_japan=random_destination_countries_for_japan,
            random_city_from_for_japan=random_city_from_for_japan,
            random_china_port=random_china_port,
            random_japan_port=random_japan_port,
            random_russia_port=random_russia_port,
            random_destination_cities_for_japan=random_destination_cities_for_japan,
            random_destination_countries_for_south_korea=random_destination_countries_for_south_korea,
            random_city_from_for_south_korea=random_city_from_for_south_korea,
            random_south_korea_port=random_south_korea_port,
            random_destination_cities_for_south_korea=random_destination_cities_for_south_korea,
            routes_tons=routes_tons,
            package_weight_in_ton=package_weight_in_ton,
            n_of_transport_packages_in_container_40=n_of_transport_packages_in_container_40,
        )

        best_pls = self.get_best_pls_for_mini_routes(full_routes)

        mini_routes = [
            MiniRoute(
                from_country='Китай',
                to_country=random_destination_country_for_china,
                weight_in_ton=routes_tons[0],
                best_pls=best_pls[0],
                tons=routes_tons[0],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                ),
            ),
            MiniRoute(
                from_country='Япония',
                to_country=random_destination_countries_for_japan[0],
                weight_in_ton=routes_tons[1],
                best_pls=best_pls[1],
                tons=routes_tons[1],
                n_40_foot_containers=math.ceil(
                    routes_tons[1] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                ),
            ),
            MiniRoute(
                from_country='Япония',
                to_country=random_destination_countries_for_japan[1],
                weight_in_ton=routes_tons[2],
                best_pls=best_pls[2],
                tons=routes_tons[2],
                n_40_foot_containers=math.ceil(
                    routes_tons[2] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                ),
            ),
            MiniRoute(
                from_country='Южная Корея',
                to_country=random_destination_countries_for_south_korea[0],
                weight_in_ton=routes_tons[3],
                best_pls=best_pls[3],
                tons=routes_tons[3],
                n_40_foot_containers=math.ceil(
                    routes_tons[3] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                ),
            ),
            MiniRoute(
                from_country='Южная Корея',
                to_country=random_destination_countries_for_south_korea[1],
                weight_in_ton=routes_tons[4],
                best_pls=best_pls[4],
                tons=routes_tons[4],
                n_40_foot_containers=math.ceil(
                    routes_tons[4] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                ),
            ),
        ]

        transport_package_volume = package_size.length * package_size.width * package_size.height

        departure_points_strs = [
            f'Китай: {full_routes[0].points[0].city}',
            f'Япония: {full_routes[4].points[0].city}',
            f'Южная Корея: {full_routes[6].points[0].city}',
        ]
        destination_points_codes = [
            full_routes[0].points[-1].code,
            full_routes[4].points[-1].code,
            full_routes[5].points[-1].code,
            full_routes[6].points[-1].code,
            full_routes[7].points[-1].code,
        ]
        ports_points_codes = set()
        borders_points_codes = set()
        terminals_points_codes = set([p.code for p in pr2_class_info.all_points if p.is_fake and p.type == 'TERMINAL'])
        all_points = [p for p in pr2_class_info.all_points if p.is_fake and p.type == 'TERMINAL']
        all_points.extend([p for p in pr2_class_info.all_points if p.is_fake and p.type == 'PORT'])
        all_points.extend(
            [
                full_routes[0].points[-1],
                full_routes[4].points[-1],
                full_routes[5].points[-1],
                full_routes[6].points[-1],
                full_routes[7].points[-1],
            ]
        )
        for r in full_routes:
            for p in r.points:
                if p.type == 'PORT':
                    ports_points_codes.add(p.code)
                    if p not in all_points:
                        all_points.append(p)
                if p.type == 'BORDER':
                    borders_points_codes.add(p.code)
                    if p not in all_points:
                        all_points.append(p)
                if p.type == 'TERMINAL':
                    terminals_points_codes.add(p.code)
                    if p not in all_points:
                        all_points.append(p)

        ports_points_codes = list(ports_points_codes)
        borders_points_codes = list(borders_points_codes)
        terminals_points_codes = list(terminals_points_codes)

        random.shuffle(all_points)

        source_data = PR2SourceData(
            mini_routes=mini_routes,
            full_routes=full_routes,
            package_size=package_size,
            package_weight_in_ton=package_weight_in_ton,
            transport_package_volume=round(transport_package_volume, 2),
            number_of_packages_in_20_foot_container=n_of_transport_packages_in_container_20,
            number_of_packages_in_40_foot_container=n_of_transport_packages_in_container_40,
            loading_volume_20_foot_container=32.3,
            loading_volume_40_foot_container=65.7,
            all_points=all_points,
            departure_points_strs=departure_points_strs,
            destination_points_codes=destination_points_codes,
            ports_points_codes=ports_points_codes,
            borders_points_codes=borders_points_codes,
            terminals_points_codes=terminals_points_codes,
        )

        legend = """Компания имеет производственные мощности в Китае, отправляя свою продукцию в Европу преимущественно морским транспортом в 20-футовых контейнерах с продолжительностью доставки более 40 суток.
С учётом значительной продолжительности доставки продукции и случившегося кризиса у поставщика транспортных услуг, от существующей схемы Компания планирует отказаться. 
Кроме того, в условиях увеличения спроса на производимую продукцию Компания расширила географию присутствия, разместив дополнительные производственные мощности в Японии и Южной Корее и рассматривает новые цепи поставок продукции.
В связи с повышением привлекательности ускоренных контейнерных сервисов через Казахстан, Монголию и Россию, Компания планирует использовать новые маршруты и технологии доставки продукции. 
Перед Логистическим департаментом поставлена задача поиска оптимальных маршрутов цепей поставок продукции в страны Европы. Выполнение задачи поручено группе инициативных логистов.
"""

        explanation = """Вы представляете сотрудника Логистического департамента Компании. Для выполнения поставленной задачи необходимо:
1.	Учитывая, что перевозка осуществлялась в 20-футовых контейнерах, обосновать эффективность использования 40-футовых контейнеров с учётом максимального использования их вместимости и грузоподъемности 
2.	Рассчитать необходимое количество 40-футовых контейнеров для каждой цепи поставок продукции
3.	Сформировать возможные маршруты доставки 
4.	Детализировать маршруты по порядку проследования через транзитные страны 
5.	Рассчитать стоимость вариантов доставки для всех маршрутов по представленным ставкам логистических провайдеров 
6.	Выбрать риски организации доставки для всех маршрутов
7.	Выбрать минимальное по стоимости предложение провайдера и оптимальную комбинацию предложений по всем цепям поставок продукции
8.	Дать рекомендации по реализации вариантов с учетом рисков"""

        event = PR2ClassEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            users_ids=self.users_ids,
            current_step=zero_step,
            source_data=source_data,
            legend=legend,
            explanation=explanation,
        )

        event_db = self.db[CollectionNames.EVENTS.value].insert_one(event.dict())

        event_db = self.db[CollectionNames.EVENTS.value].find_one({'_id': event_db.inserted_id})

        return normalize_mongo(event_db, EventInfo)

    def get_current_step(self, event: Union[PR2ClassEvent, Type[PR2ClassEvent]]):
        if event.is_finished:
            return CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        if event.current_step.code == 'SCREEN_1_INSTRUCTION_WITH_LEGEND':
            return self._get_screen_1_step_response(event)
        elif event.current_step.code == 'SCREEN_2_TASK_DESCRIPTION':
            return self._get_screen_2_step_response(event)
        elif event.current_step.code == 'SCREEN_3_SOURCE_DATA_FULL_ROUTES':
            return self._get_screen_3_step_response(event)

        elif event.current_step.code in (
            'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME',
            'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME',
            'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER',
            'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
            'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY',
        ):
            return self._get_screen_4_20_step_response(event, int(event.current_step.code[27]))

        elif event.current_step.code in (
            'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME',
            'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME',
            'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER',
            'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
            'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY',
        ):
            return self._get_screen_4_40_step_response(event, int(event.current_step.code[27]))

        elif event.current_step.code == 'SCREEN_5_DESCRIBE_CONTAINER_SELECTION':
            return self._get_describe_container_selection(event)

        elif event.current_step.code in (
            'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_1',
            'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_2',
            'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_3',
            'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_4',
            'SCREEN_6_40_CONTAINERS_NUMBER_ROUTE_5',
        ):
            return self._get_containers_number_40_step_response(event)

        elif event.current_step.code == 'SCREEN_7_SOURCE_DATA_CHOOSE_DESTINATIONS':
            return self._get_source_data_choose_destinations_step_response(event)

        elif event.current_step.code == 'SCREEN_7_SOURCE_DATA_CHOOSE_PORTS':
            return self._get_source_data_choose_ports_step_response(event)

        elif event.current_step.code == 'SCREEN_7_SOURCE_DATA_CHOOSE_BORDER':
            return self._get_source_data_choose_border_step_response(event)

        elif event.current_step.code in (
            'SCREEN_8_MAP_ROUTE_1',
            'SCREEN_8_MAP_ROUTE_2',
            'SCREEN_8_MAP_ROUTE_3',
            'SCREEN_8_MAP_ROUTE_4',
            'SCREEN_8_MAP_ROUTE_5',
            'SCREEN_8_MAP_ROUTE_6',
            'SCREEN_8_MAP_ROUTE_7',
            'SCREEN_8_MAP_ROUTE_8',
        ):
            return self._get_map_route_step_response(event, int(event.current_step.code[-1]) - 1)

        elif event.current_step.code == 'SCREEN_9_FORMED_ROUTES_TABLE':
            return self._get_formed_routes_table_step_response(event)

        elif event.current_step.code in [
            'SCREEN_10_RISKS_1',
            'SCREEN_10_RISKS_2',
            'SCREEN_10_RISKS_3',
            'SCREEN_10_RISKS_4',
        ]:
            return self._get_risks_step_response(event, int(event.current_step.code[-1]) - 1)

        elif event.current_step.code == 'SCREEN_10_RISKS_TOTAL':
            return self._get_risks_total(event)

        elif event.current_step.code == 'SCREEN_10_FULL_ROUTES_WITH_PLS':
            return self._get_full_routes_with_pls_step_response(event)

        elif event.current_step.code == 'SCREEN_11_OPTIMAL_RESULTS_3PL1':
            return self._get_optimal_results_step_response(event, 1)

        elif event.current_step.code == 'SCREEN_11_OPTIMAL_RESULTS_3PL2':
            return self._get_optimal_results_step_response(event, 2)

        elif event.current_step.code == 'SCREEN_11_OPTIMAL_RESULTS_3PL3':
            return self._get_optimal_results_step_response(event, 3)

        elif event.current_step.code == 'SCREEN_11_OPTIMAL_RESULTS_COMBO':
            return self._get_optimal_results_step_response(event, 4)

        # TODO
        elif event.current_step.code == 'SCREEN_12_OPTIMAL_WITH_RISKS':
            return self._get_optimal_with_risks_step_response(event)

        # TODO
        elif event.current_step.code == 'SCREEN_13_CHOOSE_LOGIST':
            return self._get_choose_logist_step_response(event)

        raise Exception(f'Такой current_step.code не найден. {event.current_step.code}')

    @staticmethod
    def _get_source_data_choose_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        all_fake_points = [p for p in pr2_class_info.all_points if p.is_fake == True]
        all_points_from_source_data = []
        for r in event.source_data.full_routes:
            all_points_from_source_data.extend(r.points)

        all_points = [*all_fake_points, *all_points_from_source_data]
        random.shuffle(all_points)

        step_response.all_points = all_points

        step_response.departure_points = [
            f'Китай: {event.source_data.full_routes[0].points[0].city}',
            f'Япония: {event.source_data.full_routes[4].points[0].city}',
            f'Южная Корея: {event.source_data.full_routes[6].points[0].city}',
        ]

        step_response.screen_texts = ['Заполните таблицу объектов для формирования карты маршрутов']

        return step_response

    @staticmethod
    def _get_choose_logist_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        return step_response

    @staticmethod
    def _get_optimal_with_risks_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        pl1_result = round(
            sum([r.best_pls[0].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        pl2_result = round(
            sum([r.best_pls[1].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        pl3_result = round(
            sum([r.best_pls[2].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        combo_result = round(
            sum([r.best_pls[3].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )

        step_response.pl1_formula = (
            f'{pl1_result}: {"-".join([str(r.best_pls[0].index) for r in event.source_data.mini_routes])}'
        )
        step_response.pl2_formula = (
            f'{pl2_result}: {"-".join([str(r.best_pls[1].index) for r in event.source_data.mini_routes])}'
        )
        step_response.pl3_formula = (
            f'{pl3_result}: {"-".join([str(r.best_pls[2].index) for r in event.source_data.mini_routes])}'
        )
        step_response.combo_formula = (
            f'{combo_result}: {"-".join([str(r.best_pls[3].index) for r in event.source_data.mini_routes])}'
        )

        random.shuffle(pr2_class_info.all_risks)
        step_response.pl1_risks = pr2_class_info.all_risks[:3]
        random.shuffle(pr2_class_info.all_risks)
        step_response.pl2_risks = pr2_class_info.all_risks[:4]
        random.shuffle(pr2_class_info.all_risks)
        step_response.pl3_risks = pr2_class_info.all_risks[:2]
        random.shuffle(pr2_class_info.all_risks)
        step_response.combo_risks = pr2_class_info.all_risks[:5]

        step_response.screen_texts = [
            'Выбрать минимальное по стоимости предложение провайдера и самую оптимальную комбинацию предложений по всем цепям поставок и дать рекомендации по реализации проекта'
        ]

        return step_response

    def get_best_pls_for_mini_routes(self, full_routes: list[FullRoute]):
        index_by_route_pl = {}

        counter = 1
        for route_index, route in enumerate(full_routes):
            for pl_index, pl in enumerate(route.three_pls_bets):
                if pl:
                    index_by_route_pl[(route_index, pl_index)] = counter
                    counter += 1

        best_pls = []
        route_1_best_pl1 = None  # (index, value)
        route_1_best_pl2 = None  # (index, value)
        route_1_best_pl3 = None  # (index, value)

        for route_index, route in enumerate(full_routes[:4]):
            if route.three_pls_bets[0] and (
                route_1_best_pl1 is None or route.three_pls_bets[0] < route_1_best_pl1.value
            ):
                route_1_best_pl1 = BestPL(index=index_by_route_pl[(route_index, 0)], value=route.three_pls_bets[0])
            if route.three_pls_bets[1] and (
                route_1_best_pl2 is None or route.three_pls_bets[1] < route_1_best_pl2.value
            ):
                route_1_best_pl2 = BestPL(index=index_by_route_pl[(route_index, 1)], value=route.three_pls_bets[1])
            if route.three_pls_bets[2] and (
                route_1_best_pl3 is None or route.three_pls_bets[2] < route_1_best_pl3.value
            ):
                route_1_best_pl3 = BestPL(index=index_by_route_pl[(route_index, 2)], value=route.three_pls_bets[2])

        route_1_best = route_1_best_pl1
        for pl in (route_1_best_pl2, route_1_best_pl3):
            if pl.value < route_1_best.value:
                route_1_best = pl

        best_pls.append([route_1_best_pl1, route_1_best_pl2, route_1_best_pl3, route_1_best])

        route_2_best_pl1, route_2_best_pl2, route_2_best_pl3, route_2_best = self.get_best_pls(
            full_routes[4], 4, index_by_route_pl
        )
        best_pls.append([route_2_best_pl1, route_2_best_pl2, route_2_best_pl3, route_2_best])

        route_3_best_pl1, route_3_best_pl2, route_3_best_pl3, route_3_best = self.get_best_pls(
            full_routes[5], 5, index_by_route_pl
        )
        best_pls.append([route_3_best_pl1, route_3_best_pl2, route_3_best_pl3, route_3_best])

        route_4_best_pl1, route_4_best_pl2, route_4_best_pl3, route_4_best = self.get_best_pls(
            full_routes[6], 6, index_by_route_pl
        )
        best_pls.append([route_4_best_pl1, route_4_best_pl2, route_4_best_pl3, route_4_best])

        route_5_best_pl1, route_5_best_pl2, route_5_best_pl3, route_5_best = self.get_best_pls(
            full_routes[7], 7, index_by_route_pl
        )
        best_pls.append([route_5_best_pl1, route_5_best_pl2, route_5_best_pl3, route_5_best])

        return best_pls

    @staticmethod
    def get_random_package_size():
        all_package_size_combinations = [
            PackageSize(length=0.8, width=1.2, height=0.8),
            PackageSize(length=0.8, width=1.2, height=0.9),
            PackageSize(length=0.8, width=1.2, height=1),
            PackageSize(length=0.8, width=1.2, height=1.1),
            PackageSize(length=1, width=1.2, height=1),
            PackageSize(length=1, width=1.2, height=1.1),
        ]
        return random.choice(all_package_size_combinations)

    def _get_optimal_results_step_response(self, event, row_index: int):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)
        step_response.screen_texts = [
            'Выбрать минимальное по стоимости предложение провайдера и самую оптимальную комбинацию предложений по всем цепям поставок и дать рекомендации по реализации проекта'
        ]

        pl1_result = round(
            sum([r.best_pls[0].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        pl2_result = round(
            sum([r.best_pls[1].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        pl3_result = round(
            sum([r.best_pls[2].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )
        combo_result = round(
            sum([r.best_pls[3].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2
        )

        if row_index > 1:
            step_response.pl1_formula = (
                f'{pl1_result}: {"-".join([str(r.best_pls[0].index) for r in event.source_data.mini_routes])}'
            )

        if row_index > 2:
            step_response.pl2_formula = (
                f'{pl2_result}: {"-".join([str(r.best_pls[1].index) for r in event.source_data.mini_routes])}'
            )

        if row_index > 3:
            step_response.pl3_formula = (
                f'{pl3_result}: {"-".join([str(r.best_pls[2].index) for r in event.source_data.mini_routes])}'
            )
            step_response.combo_formula = (
                f'{combo_result}: {"-".join([str(r.best_pls[3].index) for r in event.source_data.mini_routes])}'
            )

        return step_response

    @staticmethod
    def get_best_pls(route, route_index: int, index_by_route_pl: dict):
        best_pl1: Optional[BestPL] = None
        best_pl2: Optional[BestPL] = None
        best_pl3: Optional[BestPL] = None

        if route.three_pls_bets[0] and (best_pl1 is None or route.three_pls_bets[0] < best_pl1.value):
            best_pl1 = BestPL(index=index_by_route_pl[(route_index, 0)], value=route.three_pls_bets[0])
        if route.three_pls_bets[1] and (best_pl2 is None or route.three_pls_bets[1] < best_pl2.value):
            best_pl2 = BestPL(index=index_by_route_pl[(route_index, 1)], value=route.three_pls_bets[1])
        if route.three_pls_bets[2] and (best_pl3 is None or route.three_pls_bets[2] < best_pl3.value):
            best_pl3 = BestPL(index=index_by_route_pl[(route_index, 2)], value=route.three_pls_bets[2])

        best = best_pl1
        for pl in (best_pl2, best_pl3):
            if pl.value < best.value:
                best = pl

        return best_pl1, best_pl2, best_pl3, best

    @staticmethod
    def _get_risks_total(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)
        step_response.screen_texts = ['Итоговая таблица маршрутов с рисками']
        step_response.risks_chosen_by_user = event.risks_chosen_by_user
        return step_response

    @staticmethod
    def _get_full_routes_with_pls_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.screen_texts = [
            'Рассчитать стоимость доставки для всех маршрутов доставки по ставкам логистических провайдеров'
        ]

        pl_routes = []
        counter = 1
        mini_route_index_by_full_route_index = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 3, 7: 4}
        for route_index, route in enumerate(event.source_data.full_routes):
            for i, pl in enumerate(route.three_pls_bets):
                if pl:
                    mini_route_index = mini_route_index_by_full_route_index[route_index]
                    containers_num = event.source_data.mini_routes[mini_route_index].n_40_foot_containers
                    pl_routes.append(
                        PLRoute(
                            supply_chain=f'{route.country_from} - {route.country_to}',
                            route_number=counter,
                            through=f'{route.through}',
                            provider=f'3PL{i+1}',
                            containers_num=containers_num,
                            pl_bet=pl,
                            delivery_price_formula=f'{pl} * {containers_num} = {pl * containers_num}',
                            full_route_index=route_index,
                        )
                    )
                    counter += 1

        n_of_transport_packages_in_container_40 = math.floor(
            math.floor(12 / event.source_data.package_size.length)
            * math.floor(2.33 / event.source_data.package_size.width)
            * math.floor(2.35 / event.source_data.package_size.height)
        )

        mini_routes_hints = [
            MiniRouteHint(
                route=f'{r.from_country} - {r.to_country}',
                tons=r.weight_in_ton,
                n_40_containers_formula=f'{r.weight_in_ton} / ({n_of_transport_packages_in_container_40} * {event.source_data.package_weight_in_ton}) = {r.n_40_foot_containers}',
            )
            for r in event.source_data.mini_routes
        ]

        full_routes_hints = [
            FullRouteHint(route=f'{r.country_from} - {r.country_to}', through=r.through, pls=r.three_pls_bets,)
            for r in event.source_data.full_routes
        ]

        first_pl_routes = [pl for pl in pl_routes if pl.full_route_index < 4]
        second_pl_routes = [pl for pl in pl_routes if pl.full_route_index in (4, 5)]
        third_pl_routes = [pl for pl in pl_routes if pl.full_route_index in (6, 7)]

        first_mini_routes_hints = [mini_routes_hints[0]]
        second_mini_routes_hints = [mini_routes_hints[1], mini_routes_hints[2]]
        third_mini_routes_hints = [mini_routes_hints[3], mini_routes_hints[4]]

        first_full_routes_hints = full_routes_hints[:4]
        second_full_routes_hints = full_routes_hints[4:6]
        third_full_routes_hints = full_routes_hints[6:]

        step_response.pl_routes = [first_pl_routes, second_pl_routes, third_pl_routes]
        step_response.mini_routes_hints = [first_mini_routes_hints, second_mini_routes_hints, third_mini_routes_hints]
        step_response.full_routes_hints = [first_full_routes_hints, second_full_routes_hints, third_full_routes_hints]

        return step_response

    @staticmethod
    def _get_risks_step_response(event, route_index: int):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        route_names = [
            'МАРШРУТ ЧЕРЕЗ РОССИЮ (ЧЕРЕЗ ЗАБАЙКАЛЬСК И БРЕСТ)',
            'Маршрут через Монголию (через Наушки и Брест)',
            'Маршрут через Казахстан (через Достык или Алтынколь и Брест)',
            'Маршрут через МТП России',
        ]

        step_response.screen_texts = [
            'Выберите последовательно риски маршрута по степени их влияния на увеличение сроков доставки и непредвиденных затрат',
            route_names[route_index],
        ]

        step_response.risks = pr2_class_info.all_risks[route_index]
        return step_response

    @staticmethod
    def _get_formed_routes_table_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)
        step_response.screen_texts = [
            'Вы сформировали все возможные маршруты доставки в соответствии\nс '
            'предложенными сервисами для каждой цепи поставок\n'
            'с детализацией по пунктам маршрута'
        ]
        step_response.full_routes = event.source_data.full_routes
        return step_response

    @staticmethod
    def _get_map_route_step_response(event, route_index):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        mini_route_index_by_route_index = {
            0: 0,
            1: 0,
            2: 0,
            3: 0,
            4: 1,
            5: 2,
            6: 3,
            7: 4,
        }

        only_borders_text = 'последовательно выбирая погранпереходы на карте. Вы можете предварительно изучить объекты, кликнув\nпо ним.'
        ports_and_borders_text = 'последовательно выбирая порты и погранпереходы на карте. Вы можете предварительно изучить объекты, кликнув по ним.'

        mini_route_index = mini_route_index_by_route_index[route_index]

        step_response.screen_texts = [
            f'Сформируйте маршрут {event.source_data.mini_routes[mini_route_index].from_country}-'
            f'{event.source_data.mini_routes[mini_route_index].to_country} {event.source_data.full_routes[route_index].through}, '
            f'{only_borders_text if route_index <= 2 else ports_and_borders_text}'
        ]

        all_point_cities_from_routes = []
        for r in event.source_data.full_routes:
            all_point_cities_from_routes.extend(r.points)

        all_points_codes_to_show = []
        for p in pr2_class_info.all_points:
            if p.city in all_point_cities_from_routes or p.is_fake:
                all_points_codes_to_show.append(p.code)

        all_points_codes_to_show.extend([p.code for p in event.source_data.full_routes[route_index].points])

        points_to_show_set = set(all_points_codes_to_show)
        for p in pr2_class_info.all_points:
            if p.type == 'BORDER':
                points_to_show_set.add(p.code)

        all_points_codes_to_show = list(points_to_show_set)

        step_response.start_point_code = event.source_data.full_routes[route_index].points[0].code
        step_response.end_point_code = event.source_data.full_routes[route_index].points[-1].code
        step_response.route_length = len(event.source_data.full_routes[route_index].points)
        step_response.points_codes_to_show = all_points_codes_to_show
        step_response.right_route_codes = [p.code for p in event.source_data.full_routes[route_index].points]

        points = event.source_data.full_routes[route_index].points

        step_response.route_parts = [
            RoutePart(from_code=points[i].code, to_code=points[i + 1].code) for i in range(len(points) - 1)
        ]

        return step_response

    @staticmethod
    def _get_containers_number_20_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        n_of_transport_packages_in_container_20 = math.floor(
            (5.9 / event.source_data.package_size.length)
            * (2.33 / event.source_data.package_size.width)
            * (2.35 / event.source_data.package_size.height)
        )

        step_response.screen_texts = ['Расчёт необходимого количества 20-футовых контейнеров для каждой цепи продукции']
        step_response.mini_routes = event.source_data.mini_routes
        step_response.package_weight_in_ton = event.source_data.package_weight_in_ton
        step_response.number_of_packages_in_container = n_of_transport_packages_in_container_20

        return step_response

    @staticmethod
    def _get_containers_number_40_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)
        mini_routes = event.source_data.mini_routes

        right_formulas = [
            [
                f'{mini_routes[0].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{mini_routes[0].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ],
            [
                f'{mini_routes[1].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{mini_routes[1].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ],
            [
                f'{mini_routes[2].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{mini_routes[2].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ],
            [
                f'{mini_routes[3].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{mini_routes[3].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ],
            [
                f'{mini_routes[4].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})',
                f'{mini_routes[4].weight_in_ton}/({event.source_data.package_weight_in_ton:g}*{event.source_data.number_of_packages_in_40_foot_container})',
            ],
        ]

        right_formulas_with_answer = [
            f'{mini_routes[0].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})={mini_routes[0].n_40_foot_containers}',
            f'{mini_routes[1].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})={mini_routes[1].n_40_foot_containers}',
            f'{mini_routes[2].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})={mini_routes[2].n_40_foot_containers}',
            f'{mini_routes[3].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})={mini_routes[3].n_40_foot_containers}',
            f'{mini_routes[4].weight_in_ton}/({event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton:g})={mini_routes[4].n_40_foot_containers}',
        ]

        step_response.screen_texts = ['Расчёт необходимого количества 40-футовых контейнеров для каждой цепи продукции']

        step_response.container_routes_with_formulas = [
            ContainerRoute(
                route=f'{mini_routes[i].from_country} - {mini_routes[i].to_country}',
                weight_in_tons=mini_routes[i].weight_in_ton,
                formulas=right_formulas[i],
                formula_with_answer=right_formulas_with_answer[i],
            )
            for i in range(5)
        ]

        step_response.number_of_packages_in_20_foot_container = (
            event.source_data.number_of_packages_in_20_foot_container
        )
        step_response.number_of_packages_in_40_foot_container = (
            event.source_data.number_of_packages_in_40_foot_container
        )
        step_response.package_weight_in_ton = event.source_data.package_weight_in_ton

        return step_response

    @staticmethod
    def _get_describe_container_selection(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        twenty_foot_formulas = [
            FormulaRow(name='Погрузочный объём контейнера, куб.м', formula='5,9*2,33*2,35=32,3'),
            FormulaRow(
                name=f'Объём транспортного пакета, куб.м',
                formula=f'{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}='
                f'{round(event.source_data.package_size.length * event.source_data.package_size.width * event.source_data.package_size.height, 2)}',
            ),
            FormulaRow(
                name=f'Количество транспортных пакетов, размещаемых в контейнере',
                formula=f'(5,9/{event.source_data.package_size.length})*'
                f'(2,33/{event.source_data.package_size.width})*'
                f'(2,35/{event.source_data.package_size.height})={event.source_data.number_of_packages_in_20_foot_container}',
            ),
            FormulaRow(
                name=f'Коэффициент использования вместимости',
                formula=f'{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.transport_package_volume}/32,3='
                f'{round(event.source_data.number_of_packages_in_20_foot_container * event.source_data.transport_package_volume / 32.3, 2)}',
            ),
            FormulaRow(
                name=f'Коэффициент использования грузоподъёмности',
                formula=f'{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}/21.8='
                f'{round(event.source_data.number_of_packages_in_20_foot_container * event.source_data.package_weight_in_ton / 21.8, 2)}',
            ),
        ]
        twenty_foot_container_result = ContainerResult(
            header='Обоснование эффективности использования 20-футовых контейнеров с учётом максимального использования их вместимости',
            rows=twenty_foot_formulas,
        )

        forty_foot_formulas = [
            FormulaRow(name='Погрузочный объём контейнера, куб.м', formula='12*2,33*2,35=65,7'),
            FormulaRow(
                name=f'Объём транспортного пакета, куб.м',
                formula=f'{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}='
                f'{round(event.source_data.package_size.length * event.source_data.package_size.width * event.source_data.package_size.height, 2)}',
            ),
            FormulaRow(
                name=f'Количество транспортных пакетов, размещаемых в контейнере',
                formula=f'(12/{event.source_data.package_size.length})*'
                f'(2,33/{event.source_data.package_size.width})*'
                f'(2,35/{event.source_data.package_size.height})={event.source_data.number_of_packages_in_40_foot_container}',
            ),
            FormulaRow(
                name=f'Коэффициент использования вместимости',
                formula=f'{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.transport_package_volume}/65,7='
                f'{round(event.source_data.number_of_packages_in_40_foot_container * event.source_data.transport_package_volume / 65.7, 2)}',
            ),
            FormulaRow(
                name=f'Коэффициент использования грузоподъёмности',
                formula=f'{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}/21.8='
                f'{round(event.source_data.number_of_packages_in_40_foot_container * event.source_data.package_weight_in_ton / 26.4, 2)}',
            ),
        ]

        forty_foot_container_result = ContainerResult(
            header='Обоснование эффективности использования 40-футовых контейнеров с учётом максимального использования их вместимости',
            rows=forty_foot_formulas,
        )

        step_response.containers_results = [twenty_foot_container_result, forty_foot_container_result]

        return step_response

    @staticmethod
    def _get_screen_4_20_step_response(event, formula_num: int):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.screen_texts = [
            'Обоснование эффективности использования 20-футовых контейнеров '
            'с учётом максимального использования их вместимости и грузоперевозки'
        ]

        step_response.container_foots = 20

        step_response.container_load_capacity = 21.8
        step_response.container_length = 5.9
        step_response.container_width = 2.33
        step_response.container_height = 2.35

        step_response.package_length = event.source_data.package_size.length
        step_response.package_width = event.source_data.package_size.width
        step_response.package_height = event.source_data.package_size.height
        step_response.package_weight_in_ton = event.source_data.package_weight_in_ton

        step_response.extra_button_numbers = []

        if formula_num >= 2:
            step_response.extra_button_numbers.append(
                ButtonNumber(text='Погрузочный объём', value=event.source_data.loading_volume_20_foot_container)
            )

        if formula_num >= 3:
            step_response.extra_button_numbers.append(
                ButtonNumber(text='Объём пакета', value=event.source_data.transport_package_volume)
            )

        if formula_num >= 4:
            step_response.extra_button_numbers.append(
                ButtonNumber(
                    text='Кол-во пакетов в контейнере', value=event.source_data.number_of_packages_in_20_foot_container
                )
            )

        return step_response

    @staticmethod
    def _get_screen_4_40_step_response(event, formula_num: int):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.screen_texts = [
            'Обоснование эффективности использования 40-футовых контейнеров '
            'с учётом максимального использования их вместимости и грузоперевозки'
        ]

        step_response.container_foots = 40

        step_response.container_load_capacity = 26.4
        step_response.container_length = 12
        step_response.container_width = 2.33
        step_response.container_height = 2.35

        step_response.package_length = event.source_data.package_size.length
        step_response.package_width = event.source_data.package_size.width
        step_response.package_height = event.source_data.package_size.height
        step_response.package_weight_in_ton = event.source_data.package_weight_in_ton

        step_response.extra_button_numbers = []

        if formula_num >= 2:
            step_response.extra_button_numbers.append(
                ButtonNumber(text='Погрузочный объём', value=event.source_data.loading_volume_40_foot_container)
            )

        if formula_num >= 3:
            step_response.extra_button_numbers.append(
                ButtonNumber(text='Объём пакета', value=event.source_data.transport_package_volume)
            )

        if formula_num >= 4:
            step_response.extra_button_numbers.append(
                ButtonNumber(
                    text='Кол-во пакетов в контейнере', value=event.source_data.number_of_packages_in_40_foot_container
                )
            )

        return step_response

    @staticmethod
    def _get_screen_3_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.screen_texts = [
            'На основе аналитики рынка ускоренных железнодорожных и интермодальных контейнерных сервисов '
            '"Door to Door", выбраны предложения ставок логистических провайдеров 3PL. Срок доставки по любому из маршрутов не превышает 25 суток, '
            'что устраивает компанию.'
        ]
        all_point_names = set()
        for r in event.source_data.full_routes:
            for p in r.points:
                all_point_names.add(p.city)
        step_response.screen_texts.append(
            f'Предложенные сервисы осуществляются в 40-футовых контейнерах через следующие пункты (порт, погранпереход, терминал): '
            f"{', '.join(list(all_point_names))}"
        )

        step_response.full_routes = event.source_data.full_routes

        return step_response

    @staticmethod
    def _get_screen_2_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.screen_texts = [
            'Оптимальные маршруты цепей поставок продукции',
            'На основании изучения рынка и заключённых договоров на поставку продукции сформированы 5 новых цепей поставок продукции ежемесячно '
            'при разных условиях инкотермс:',
            'Продукция предоставляется к перевозке в сформированных на подоннах транспорных пакетах',
        ]

        step_response.package_length = event.source_data.package_size.length
        step_response.package_width = event.source_data.package_size.width
        step_response.package_height = event.source_data.package_size.height

        # step_response.mini_routes = event.source_data.mini_routes
        #
        # step_response.screen_texts = [
        #     (
        #         f'Продукция предоставляется к перевозке в сформированных на поддонах '
        #         f'транспортных пакетах размером {event.source_data.package_size.length}мм*'
        #         f'{event.source_data.package_size.width}мм*'
        #         f'{event.source_data.package_size.height}мм (Д*Ш*В)'
        #         f' комбинации весом {event.source_data.package_weight_in_ton} т.'
        #     ),
        #     f'На основании изучения рынка и заключённых договоров на поставку продукции сформированы 5 новых цепей поставок продукции ежемесячно при разных условиях Инкотермс: '
        # ]

        return step_response

    @staticmethod
    def _get_screen_1_step_response(event):
        step_response = CurrentStepResponse(is_finished=event.is_finished, current_step=event.current_step)

        step_response.legend = event.legend
        step_response.explanation = event.explanation
        step_response.screen_texts = ['Оптимальные маршруты цепей поставок продукции']

        return step_response

    @staticmethod
    def get_point_by_city_name(city: str) -> PR2Point:
        for point in pr2_class_info.all_points:
            if point.city == city:
                return point
        raise Exception('Точка не найдена')

    def get_full_routes(
        self,
        random_destination_country_for_china,
        random_city_from_for_china,
        random_destination_city_for_china,
        chosen_dynamic_border,
        random_destination_countries_for_japan,
        random_city_from_for_japan,
        random_china_port,
        random_japan_port,
        random_russia_port,
        random_destination_cities_for_japan,
        random_destination_countries_for_south_korea,
        random_city_from_for_south_korea,
        random_south_korea_port,
        random_destination_cities_for_south_korea,
        routes_tons,
        package_weight_in_ton,
        n_of_transport_packages_in_container_40,
    ) -> list[FullRoute]:
        random_start = random.randint(20, 85)

        def is_valid(rows):
            # 1. Не должно быть одинаковых чисел в одной строчке (для всех маршрутов)
            for row in rows:
                nums_without_nones = [num for num in row if num is not None]
                if len(set(nums_without_nones)) != len(nums_without_nones):
                    return False

            # 2. Не должно быть одинаковых чисел в одном столбце для первых 4 маршрутов
            pl1_nums = []
            pl2_nums = []
            pl3_nums = []
            for row in rows[:4]:
                if row[0] is not None:
                    pl1_nums.append(row[0])
                if row[1] is not None:
                    pl2_nums.append(row[1])
                if row[2] is not None:
                    pl3_nums.append(row[2])
            if len(pl1_nums) == 0 or len(pl2_nums) == 0 or len(pl3_nums) == 0:
                return False
            all_nums = pl1_nums + pl2_nums + pl3_nums
            min_num_in_combo = min(all_nums)
            if (
                all_nums.count(min_num_in_combo) > 1
                or len(pl1_nums) != len(set(pl1_nums))
                or len(pl2_nums) != len(set(pl2_nums))
                or len(pl3_nums) != len(set(pl3_nums))
            ):
                return False

            pl1_nums_2 = []
            pl2_nums_2 = []
            pl3_nums_2 = []
            for row in rows:
                if row[0] is not None:
                    pl1_nums_2.append(row[0])
                if row[1] is not None:
                    pl2_nums_2.append(row[1])
                if row[2] is not None:
                    pl3_nums_2.append(row[2])

            if (
                len(pl1_nums_2) != len(set(pl1_nums_2))
                or len(pl2_nums_2) != len(set(pl2_nums_2))
                or len(pl3_nums_2) != len(set(pl3_nums_2))
            ):
                return False

            pl1_result = min(pl1_nums) + rows[4][0] + rows[5][0] + rows[6][0] + rows[7][0]
            pl2_result = min(pl2_nums) + rows[4][1] + rows[5][1] + rows[6][1] + rows[7][1]
            pl3_result = min(pl3_nums) + rows[4][2] + rows[5][2] + rows[6][2] + rows[7][2]

            if len(set([pl1_result, pl2_result, pl3_result])) != 3:
                return False

            return True

        all_random_3pls_grouped = None

        for attempt in range(100000):
            candidate_groups = []

            for _ in range(8):
                random_pls = random.sample(range(random_start * 100, (random_start + 15) * 100, 100), 3)
                candidate_groups.append(random_pls)

            for group_index in range(4):
                random_index_for_none = random.randint(0, 2)
                candidate_groups[group_index][random_index_for_none] = None

            if is_valid(candidate_groups):
                all_random_3pls_grouped = candidate_groups
                break

        if all_random_3pls_grouped is None:
            raise Exception('Такого не могло быть!')

        n_40_foot_containers = math.ceil(
            routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
        )
        china_route_1 = FullRoute(
            through='через Россию',
            country_from='Китай',
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name('Забайкальск'),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china),
            ],
            three_pls_bets=all_random_3pls_grouped[0],
            n_40_foot_containers=n_40_foot_containers,
        )

        china_route_2 = FullRoute(
            through='через Монголию',
            country_from='Китай',
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name('Наушки'),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china),
            ],
            three_pls_bets=all_random_3pls_grouped[1],
            n_40_foot_containers=n_40_foot_containers,
        )

        china_route_3 = FullRoute(
            through='через Казахстан',
            country_from='Китай',
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name(chosen_dynamic_border),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china),
            ],
            three_pls_bets=all_random_3pls_grouped[2],
            n_40_foot_containers=n_40_foot_containers,
        )

        china_route_4 = FullRoute(
            through='через МТП России',
            country_from='Китай',
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name(random_china_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china),
            ],
            three_pls_bets=all_random_3pls_grouped[3],
            n_40_foot_containers=n_40_foot_containers,
        )

        n_40_foot_containers = math.ceil(
            routes_tons[1] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
        )
        japan_route_1 = FullRoute(
            through='через МТП России',
            country_from='Япония',
            country_to=random_destination_countries_for_japan[0],
            weight_in_tons=routes_tons[1],
            points=[
                self.get_point_by_city_name(random_city_from_for_japan),
                self.get_point_by_city_name(random_japan_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_japan[0]),
            ],
            three_pls_bets=all_random_3pls_grouped[4],
            n_40_foot_containers=n_40_foot_containers,
        )

        n_40_foot_containers = math.ceil(
            routes_tons[2] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
        )
        japan_route_2 = FullRoute(
            through='через МТП России',
            country_from='Япония',
            country_to=random_destination_countries_for_japan[1],
            weight_in_tons=routes_tons[2],
            points=[
                self.get_point_by_city_name(random_city_from_for_japan),
                self.get_point_by_city_name(random_japan_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_japan[1]),
            ],
            three_pls_bets=all_random_3pls_grouped[5],
            n_40_foot_containers=n_40_foot_containers,
        )

        n_40_foot_containers = math.ceil(
            routes_tons[3] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
        )
        south_korea_route_1 = FullRoute(
            through='через МТП России',
            country_from='Южная Корея',
            country_to=random_destination_countries_for_south_korea[0],
            weight_in_tons=routes_tons[3],
            points=[
                self.get_point_by_city_name(random_city_from_for_south_korea),
                self.get_point_by_city_name(random_south_korea_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_south_korea[0]),
            ],
            three_pls_bets=all_random_3pls_grouped[6],
            n_40_foot_containers=n_40_foot_containers,
        )

        n_40_foot_containers = math.ceil(
            routes_tons[4] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
        )
        south_korea_route_2 = FullRoute(
            through='через МТП России',
            country_from='Южная Корея',
            country_to=random_destination_countries_for_south_korea[1],
            weight_in_tons=routes_tons[4],
            points=[
                self.get_point_by_city_name(random_city_from_for_south_korea),
                self.get_point_by_city_name(random_south_korea_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_south_korea[1]),
            ],
            three_pls_bets=all_random_3pls_grouped[7],
            n_40_foot_containers=n_40_foot_containers,
        )

        return [
            china_route_1,
            china_route_2,
            china_route_3,
            china_route_4,
            japan_route_1,
            japan_route_2,
            south_korea_route_1,
            south_korea_route_2,
        ]
