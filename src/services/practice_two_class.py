import random
from typing import Optional, Union, Type
import math
from bson import ObjectId

from constants.pr2_class_info import pr2_class_info
from db.mongo import get_db, CollectionNames
from schemas import PR2ClassEvent, CurrentStepResponse, StartEventDto, PR2Point, Step, MiniRoute, PR2SourceData, \
    PackageSize, FullRoute, ContainerResult, FormulaRow, PR2Risk, PLRoute, PLOption, BestPL, CheckpointData, \
    CheckpointResponse, EventStepResult, EventInfo, CheckpointResponseStatus
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
        is_last_attempt = (event.current_step.code == last_step_result.step_code and last_step_result.fails == 2)

        if event.current_step.code != last_step_result.step_code:
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0))

        if is_last_attempt or not is_failed:
            event.current_step = next_step
            checkpoint_response.next_step = next_step

        if is_failed:
            checkpoint_response.status = (
                CheckpointResponseStatus.FAILED.value if is_last_attempt
                else CheckpointResponseStatus.TRY_AGAIN.value
            )
        else:
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

    def checkpoint(self, event: Union[PR2ClassEvent, Type[PR2ClassEvent]], checkpoint_dto: CheckpointData):
        checkpoint_response = CheckpointResponse()

        if checkpoint_dto.step_code != event.current_step.code:
            raise Exception(f'Backend ждёт {event.current_step.code} step_code')

        if checkpoint_dto.step_code == 'SCREEN_1_INSTRUCTION_WITH_LEGEND':
            next_step = Step(
                id=1,
                code=self._get_next_code_by_id(1),
            )
            checkpoint_response.next_step = next_step
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0, )
            )
            event.current_step = next_step

        if checkpoint_dto.step_code == 'SCREEN_2_TASK_DESCRIPTION':
            next_step = Step(
                id=2,
                code=self._get_next_code_by_id(2),
            )
            checkpoint_response.next_step = next_step
            event.steps_results.append(
                EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0, )
            )
            event.current_step = next_step

        if checkpoint_dto.step_code == 'SCREEN_3_SOURCE_DATA_FULL_ROUTES':
            next_step = Step(id=3, code=self._get_next_code_by_id(3))

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME':
            next_step = Step(id=4, code=self._get_next_code_by_id(4))

            is_failed = checkpoint_dto.formula not in [
                '5.9*2.33*2.35',
                '5.9*2.33*2.35',
                '2.33*5.9*2.35',
                '2.33*2.35*5.9',
                '5.9*2.33*2.35',
                '5.9*2.35*2.33',
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME':
            next_step = Step(id=5, code=self._get_next_code_by_id(5),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}",
                f"{event.source_data.package_size.length}*{event.source_data.package_size.height}*{event.source_data.package_size.width}",
                f"{event.source_data.package_size.height}*{event.source_data.package_size.width}*{event.source_data.package_size.length}",
                f"{event.source_data.package_size.height}*{event.source_data.package_size.length}*{event.source_data.package_size.height}",
                f"{event.source_data.package_size.width}*{event.source_data.package_size.height}*{event.source_data.package_size.length}",
                f"{event.source_data.package_size.width}*{event.source_data.package_size.length}*{event.source_data.package_size.height}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER':
            next_step = Step(id=6, code=self._get_next_code_by_id(6),)

            is_failed = checkpoint_dto.formula not in [
                f"5.9/{event.source_data.package_size.length}*2.33/{event.source_data.package_size.width}*2.35/{event.source_data.package_size.height}",
                f"5.9/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}*2.33/{event.source_data.package_size.width}",
                f"2.35/{event.source_data.package_size.height}*2.33/{event.source_data.package_size.width}*5.9/{event.source_data.package_size.length}",
                f"2.35/{event.source_data.package_size.height}*5.9/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}",
                f"2.33/{event.source_data.package_size.width}*2.35/{event.source_data.package_size.height}*5.9/{event.source_data.package_size.length}",
                f"2.33/{event.source_data.package_size.width}*5.9/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION':
            next_step = Step(id=7, code=self._get_next_code_by_id(7),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.transport_package_volume}/{event.source_data.loading_volume_20_foot_container}*{event.source_data.number_of_packages_in_20_foot_container}",
                f"{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.transport_package_volume}/{event.source_data.loading_volume_20_foot_container}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY':
            next_step = Step(id=8, code=self._get_next_code_by_id(8),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}/21.8",
                f"{event.source_data.package_weight_in_ton}/21.8*{event.source_data.number_of_packages_in_20_foot_container}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME':
            next_step = Step(id=9, code=self._get_next_code_by_id(9),)

            is_failed = checkpoint_dto.formula not in [
                '12*2.33*2.35',
                '12*2.33*2.35',
                '2.33*12*2.35',
                '2.33*2.35*12',
                '12*2.33*2.35',
                '12*2.35*2.33',
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME':
            next_step = Step(id=10, code=self._get_next_code_by_id(10),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}",
                f"{event.source_data.package_size.length}*{event.source_data.package_size.height}*{event.source_data.package_size.width}",
                f"{event.source_data.package_size.height}*{event.source_data.package_size.width}*{event.source_data.package_size.length}",
                f"{event.source_data.package_size.height}*{event.source_data.package_size.length}*{event.source_data.package_size.height}",
                f"{event.source_data.package_size.width}*{event.source_data.package_size.height}*{event.source_data.package_size.length}",
                f"{event.source_data.package_size.width}*{event.source_data.package_size.length}*{event.source_data.package_size.height}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER':
            next_step = Step(id=11, code=self._get_next_code_by_id(11),)

            is_failed = checkpoint_dto.formula not in [
                f"12/{event.source_data.package_size.length}*2.33/{event.source_data.package_size.width}*2.35/{event.source_data.package_size.height}",
                f"12/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}*2.33/{event.source_data.package_size.width}",
                f"2.35/{event.source_data.package_size.height}*2.33/{event.source_data.package_size.width}*12/{event.source_data.package_size.length}",
                f"2.35/{event.source_data.package_size.height}*12/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}",
                f"2.33/{event.source_data.package_size.width}*2.35/{event.source_data.package_size.height}*12/{event.source_data.package_size.length}",
                f"2.33/{event.source_data.package_size.width}*12/{event.source_data.package_size.length}*2.35/{event.source_data.package_size.height}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION':
            next_step = Step(id=12, code=self._get_next_code_by_id(12),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.transport_package_volume}/{event.source_data.loading_volume_40_foot_container}*{event.source_data.number_of_packages_in_40_foot_container}",
                f"{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.transport_package_volume}/{event.source_data.loading_volume_40_foot_container}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY':
            next_step = Step(id=13, code=self._get_next_code_by_id(13),)

            is_failed = checkpoint_dto.formula not in [
                f"{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}/21.8",
                f"{event.source_data.package_weight_in_ton}/21.8*{event.source_data.number_of_packages_in_40_foot_container}",
            ]

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_5_DESCRIBE_CONTAINER_SELECTION':
            next_step = Step(id=14, code=self._get_next_code_by_id(14),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_6_20_CONTAINERS_NUMBER':
            next_step = Step(id=15, code=self._get_next_code_by_id(15),)

            if len(checkpoint_dto.formulas) < 5:
                raise Exception("Ожидается 5 формул")

            right_answers = [
                [
                    f"{event.source_data.mini_routes[0].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[0].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                 ],
                [
                    f"{event.source_data.mini_routes[1].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[1].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[2].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[2].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[3].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[3].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[4].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[4].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[5].weight_in_ton}/{event.source_data.number_of_packages_in_20_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[5].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_20_foot_container}"
                ]
            ]

            is_failed = False
            for i, formula in enumerate(checkpoint_dto.formulas):
                if formula not in right_answers[i]:
                    is_failed = True

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_6_40_CONTAINERS_NUMBER':
            next_step = Step(id=16, code=self._get_next_code_by_id(16),)

            if len(checkpoint_dto.formulas) < 5:
                raise Exception("Ожидается 5 формул")

            right_answers = [
                [
                    f"{event.source_data.mini_routes[0].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[0].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[1].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[1].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[2].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[2].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[3].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[3].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[4].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[4].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ],
                [
                    f"{event.source_data.mini_routes[5].weight_in_ton}/{event.source_data.number_of_packages_in_40_foot_container}*{event.source_data.package_weight_in_ton}",
                    f"{event.source_data.mini_routes[5].weight_in_ton}/{event.source_data.package_weight_in_ton}*{event.source_data.number_of_packages_in_40_foot_container}"
                ]
            ]

            is_failed = False
            for i, formula in enumerate(checkpoint_dto.formulas):
                if formula not in right_answers[i]:
                    is_failed = True

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_7_SOURCE_DATA_CHOOSE':
            next_step = Step(id=17, code=self._get_next_code_by_id(17),)

            right_departure_points_codes = [
                event.source_data.full_routes[0].points[0].code,
                event.source_data.full_routes[4].points[0].code,
                event.source_data.full_routes[6].points[0].code
            ]

            right_destination_points_codes = [
                event.source_data.full_routes[0].points[-1].code,
                event.source_data.full_routes[4].points[-1].code,
                event.source_data.full_routes[5].points[-1].code,
                event.source_data.full_routes[6].points[-1].code,
                event.source_data.full_routes[7].points[-1].code,
            ]

            right_ports_codes = set([p for p in pr2_class_info.all_points if p.is_fake and p.type == "PORT"])
            right_borders_codes = set()
            for r in event.source_data.full_routes:
                for p in r.points:
                    if p.type == "PORT":
                        right_ports_codes.add(p.code)
                    if p.type == "BORDER":
                        right_borders_codes.add(p.code)

            is_failed = (
                    len(checkpoint_dto.source_data_choose_screen.departure_points_codes) != 3 or
                    len(checkpoint_dto.source_data_choose_screen.destination_points_codes) != 5 or
                    len(checkpoint_dto.source_data_choose_screen.ports_points_codes) != len(right_ports_codes) or
                    len(checkpoint_dto.source_data_choose_screen.borders_points_codes) != len(right_borders_codes)
            )

            if (
                checkpoint_dto.source_data_choose_screen.departure_points_codes != right_departure_points_codes or
                checkpoint_dto.source_data_choose_screen.destination_points_codes != right_destination_points_codes or
                set(checkpoint_dto.source_data_choose_screen.ports_points_codes) != right_ports_codes or
                set(checkpoint_dto.source_data_choose_screen.borders_points_codes) != right_borders_codes
            ):
                is_failed = True

            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_1':
            next_step = Step(id=18, code=self._get_next_code_by_id(18),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[0].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_2':
            next_step = Step(id=19, code=self._get_next_code_by_id(19),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[1].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_3':
            next_step = Step(id=20, code=self._get_next_code_by_id(20),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[2].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_4':
            next_step = Step(id=21, code=self._get_next_code_by_id(21),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[3].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_5':
            next_step = Step(id=22, code=self._get_next_code_by_id(22),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[4].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_6':
            next_step = Step(id=23, code=self._get_next_code_by_id(23),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[5].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_7':
            next_step = Step(id=24, code=self._get_next_code_by_id(24),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[6].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_8_MAP_ROUTE_8':
            next_step = Step(id=25, code=self._get_next_code_by_id(25),)
            is_failed = checkpoint_dto.route_points_codes != [p.code for p in event.source_data.full_routes[7].points]
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_1':
            next_step = Step(id=26, code=self._get_next_code_by_id(26),)
            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_2':
            next_step = Step(id=27, code=self._get_next_code_by_id(27),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_3':
            next_step = Step(id=28, code=self._get_next_code_by_id(28),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_4':
            next_step = Step(id=29, code=self._get_next_code_by_id(29),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_5':
            next_step = Step(id=30, code=self._get_next_code_by_id(30),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_6':
            next_step = Step(id=31, code=self._get_next_code_by_id(31),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_7':
            next_step = Step(id=32, code=self._get_next_code_by_id(32),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_9_RISKS_8':
            next_step = Step(id=33, code=self._get_next_code_by_id(33),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_10_FULL_ROUTES_WITH_PLS':
            next_step = Step(id=34, code=self._get_next_code_by_id(34),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_11_OPTIMAL_RESULTS':
            next_step = Step(id=35, code=self._get_next_code_by_id(35),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_12_OPTIMAL_WITH_RISKS':
            next_step = Step(id=36, code=self._get_next_code_by_id(36),)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        if checkpoint_dto.step_code == 'SCREEN_13_CHOOSE_LOGIST':
            next_step = Step(id=-1, code='FINISH',)

            is_failed = False
            self.handle_checkpoint_is_failed(event, is_failed, checkpoint_response, next_step)

        self.db[CollectionNames.EVENTS.value].update_one({'_id': ObjectId(event.id)}, {'$set': event.dict()})

        return checkpoint_response

    def create(self, event_dto: StartEventDto):
        zero_step = Step(
            id=1,
            code=f'SCREEN_1_INSTRUCTION_WITH_LEGEND',
            name=f'Легенда и Инструкция',
        )

        all_destination_countries = ['Польша', 'Германия', 'Франция', 'Нидерланды', 'Бельгия', 'Чехия', 'Австрия']
        random.shuffle(all_destination_countries)
        random_destination_country_for_china = all_destination_countries[0]
        random_destination_countries_for_japan = all_destination_countries[1:3]
        random_destination_countries_for_south_korea = all_destination_countries[3:5]
        random_city_from_for_china = random.choice(['Шицзячжуан', 'Цзинань', 'Иу', 'Баодин'])
        random_city_from_for_japan = random.choice(['Киото', 'Аябе', 'Асаго', 'Мацумото'])
        random_city_from_for_south_korea = random.choice(['Сувон', 'Тэджон', 'Чханвон', 'Кванджу'])

        destination_cities_by_destination_country = {
            "Польша": ["Острава", "Лодзь"],
            "Германия": ["Лейпциг", "Аугсбург"],
            "Франция": ["Руан", "Лион"],
            "Нидерланды": ["Утрехт", "Харлем"],
            "Бельгия": ["Лёвен", "Гент"],
            "Чехия": ["Пардубице", "Пльзень"],
            "Австрия": ["Линц", "Санкт-Пёльтен"]
        }

        random_destination_city_for_china = random.choice(
            destination_cities_by_destination_country[random_destination_country_for_china]
        )

        random_destination_cities_for_japan = [
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[0]]),
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[1]])
        ]

        random_destination_cities_for_south_korea = [
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[0]]),
            random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[1]])
        ]

        dynamic_borders = ['Достык', 'Алтынкуль']
        chosen_dynamic_border = random.choice(dynamic_borders)

        random_china_port = random.choice(["Гуанчжоу", "Нинбо", "Чунцин", "Циндао"])
        random_japan_port = random.choice(["Акита", "Йокогама", "Кобе", "Нагоя"])
        random_south_korea_port = random.choice(["Пусан", "Инчон"])
        random_russia_port = random.choice(["Владивосток", "Восточный"])

        routes_tons = [
            random.randint(10, 16) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100,
            random.randint(5, 10) * 100
        ]

        package_size = self.get_random_package_size()
        package_weight_in_ton = random.randint(1, 9) / 10

        n_of_transport_packages_in_container_20 = math.floor(
            (5.9 / package_size.length)
            * (2.33 / package_size.width)
            * (2.35 / package_size.height)
        )

        n_of_transport_packages_in_container_40 = math.floor(
            (12 / package_size.length)
            * (2.33 / package_size.width)
            * (2.35 / package_size.height)
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
                from_country="Китай",
                to_country=random_destination_country_for_china,
                weight_in_ton=routes_tons[0],
                best_pls=best_pls[0],
                tons=routes_tons[0],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                )
            ),
            MiniRoute(
                from_country="Япония",
                to_country=random_destination_countries_for_japan[0],
                weight_in_ton=routes_tons[1],
                best_pls=best_pls[1],
                tons=routes_tons[1],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                )
            ),
            MiniRoute(
                from_country="Япония",
                to_country=random_destination_countries_for_japan[1],
                weight_in_ton=routes_tons[2],
                best_pls=best_pls[2],
                tons=routes_tons[2],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                )
            ),
            MiniRoute(
                from_country="Южная Корея",
                to_country=random_destination_countries_for_south_korea[0],
                weight_in_ton=routes_tons[3],
                best_pls=best_pls[3],
                tons=routes_tons[3],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                )
            ),
            MiniRoute(
                from_country="Южная Корея",
                to_country=random_destination_countries_for_south_korea[1],
                weight_in_ton=routes_tons[4],
                best_pls=best_pls[4],
                tons=routes_tons[4],
                n_40_foot_containers=math.ceil(
                    routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton)
                )
            )
        ]

        transport_package_volume = package_size.length * package_size.width * package_size.height

        source_data = PR2SourceData(
            mini_routes=mini_routes,
            full_routes=full_routes,
            package_size=package_size,
            package_weight_in_ton=random.randint(1, 9) / 10,
            transport_package_volume=round(transport_package_volume, 2),
            number_of_packages_in_20_foot_container=n_of_transport_packages_in_container_20,
            number_of_packages_in_40_foot_container=n_of_transport_packages_in_container_40,
            loading_volume_20_foot_container=32.3,
            loading_volume_40_foot_container=65.7
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
            explanation=explanation
        )

        event_db = self.db[CollectionNames.EVENTS.value].insert_one(event.dict())

        event_db = self.db[CollectionNames.EVENTS.value].find_one({'_id': event_db.inserted_id})

        return normalize_mongo(event_db, EventInfo)

    def get_current_step(self, event: Union[PR2ClassEvent, Type[PR2ClassEvent]]):
        if event.is_finished:
            return CurrentStepResponse(
                is_finished=event.is_finished,
                current_step=event.current_step
            )

        if event.current_step.code == "SCREEN_1_INSTRUCTION_WITH_LEGEND":
            return self._get_screen_1_step_response(event)
        elif event.current_step.code == "SCREEN_2_TASK_DESCRIPTION":
            return self._get_screen_2_step_response(event)
        elif event.current_step.code == "SCREEN_3_SOURCE_DATA_FULL_ROUTES":
            return self._get_screen_3_step_response(event)

        elif event.current_step.code in (
                'SCREEN_4_20_FOOT_CONTAINER_1_LOADING_VOLUME',
                'SCREEN_4_20_FOOT_CONTAINER_2_PACKAGE_VOLUME',
                'SCREEN_4_20_FOOT_CONTAINER_3_PACKAGE_NUMBER',
                'SCREEN_4_20_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
                'SCREEN_4_20_FOOT_CONTAINER_5_LOAD_CAPACITY'
        ):
            return self._get_screen_4_20_step_response(event)

        elif event.current_step.code in (
                'SCREEN_4_40_FOOT_CONTAINER_1_LOADING_VOLUME',
                'SCREEN_4_40_FOOT_CONTAINER_2_PACKAGE_VOLUME',
                'SCREEN_4_40_FOOT_CONTAINER_3_PACKAGE_NUMBER',
                'SCREEN_4_40_FOOT_CONTAINER_4_CAPACITY_UTILIZATION',
                'SCREEN_4_40_FOOT_CONTAINER_5_LOAD_CAPACITY'
        ):
            return self._get_screen_4_40_step_response(event)

        elif event.current_step.code == 'SCREEN_6_DESCRIBE_CONTAINER_SELECTION':
            return self._get_describe_container_selection(event)

        elif event.current_step.code == 'SCREEN_7_20_CONTAINERS_NUMBER':
            return self._get_containers_number_20_step_response(event)

        elif event.current_step.code == 'SCREEN_7_40_CONTAINERS_NUMBER':
            return self._get_containers_number_40_step_response(event)

        elif event.current_step.code == 'SCREEN_8_SOURCE_DATA_CHOOSE':
            return self._get_source_data_choose_step_response(event)

        elif event.current_step.code in (
                'SCREEN_9_MAP_ROUTE_1',
                'SCREEN_9_MAP_ROUTE_2',
                'SCREEN_9_MAP_ROUTE_3',
                'SCREEN_9_MAP_ROUTE_4',
                'SCREEN_9_MAP_ROUTE_5',
                'SCREEN_9_MAP_ROUTE_6',
                'SCREEN_9_MAP_ROUTE_7',
                'SCREEN_9_MAP_ROUTE_8'
        ):
            return self._get_map_route_step_response(event, int(event.current_step.code[-1]))

        elif event.current_step.code == 'SCREEN_10_FORMED_ROUTES_TABLE':
            return self._get_formed_routes_table_step_response(event)

        elif event.current_step.code in [
            'SCREEN_11_RISKS_1',
            'SCREEN_11_RISKS_2',
            'SCREEN_11_RISKS_3',
            'SCREEN_11_RISKS_4',
            'SCREEN_11_RISKS_5',
            'SCREEN_11_RISKS_6',
            'SCREEN_11_RISKS_7',
            'SCREEN_11_RISKS_8',
        ]:
            return self._get_risks_step_response(event, int(event.current_step.code[-1]))

        elif event.current_step.code == 'SCREEN_11_FULL_ROUTES_WITH_PLS':
            return self._get_full_routes_with_pls_step_response(event)

        elif event.current_step.code == 'SCREEN_12_OPTIMAL_RESULTS':
            return self._get_optimal_results_step_response(event)

        # TODO
        elif event.current_step.code == 'SCREEN_13_OPTIMAL_WITH_RISKS':
            return self._get_optimal_with_risks_step_response(event)

        # TODO
        elif event.current_step.code == 'SCREEN_14_CHOOSE_LOGIST':
            return self._get_choose_logist_step_response(event)

        raise Exception(f"Такой current_step.code не найден. {event.current_step.code}")

    @staticmethod
    def _get_source_data_choose_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = ['ЭТОТ ПОИНТ В ДОРАБОТКЕ']

        return step_response


    @staticmethod
    def _get_choose_logist_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        return step_response

    @staticmethod
    def _get_optimal_with_risks_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

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
            if route.three_pls_bets[0] and (route_1_best_pl1 is None or route.three_pls_bets[0] < route_1_best_pl1.value):
                route_1_best_pl1 = BestPL(index=index_by_route_pl[(route_index, 0)], value=route.three_pls_bets[0])
            if route.three_pls_bets[1] and (route_1_best_pl2 is None or route.three_pls_bets[1] < route_1_best_pl2.value):
                route_1_best_pl2 = BestPL(index=index_by_route_pl[(route_index, 1)], value=route.three_pls_bets[1])
            if route.three_pls_bets[2] and (route_1_best_pl3 is None or route.three_pls_bets[2] < route_1_best_pl3.value):
                route_1_best_pl3 = BestPL(index=index_by_route_pl[(route_index, 2)], value=route.three_pls_bets[2])

        route_1_best = route_1_best_pl1
        for pl in (route_1_best_pl2, route_1_best_pl3):
            if pl.value < route_1_best.value:
                route_1_best = pl

        best_pls.append([route_1_best_pl1,route_1_best_pl2,route_1_best_pl3,route_1_best])

        route_2_best_pl1, route_2_best_pl2, route_2_best_pl3, route_2_best = self.get_best_pls(
            full_routes[4],
            4,
            index_by_route_pl
        )
        best_pls.append([route_2_best_pl1, route_2_best_pl2, route_2_best_pl3, route_2_best])

        route_3_best_pl1, route_3_best_pl2, route_3_best_pl3, route_3_best = self.get_best_pls(
            full_routes[5],
            5,
            index_by_route_pl
        )
        best_pls.append([route_3_best_pl1, route_3_best_pl2, route_3_best_pl3, route_3_best])

        route_4_best_pl1, route_4_best_pl2, route_4_best_pl3, route_4_best = self.get_best_pls(
            full_routes[6],
            6,
            index_by_route_pl
        )
        best_pls.append([route_4_best_pl1, route_4_best_pl2, route_4_best_pl3, route_4_best])

        route_5_best_pl1, route_5_best_pl2, route_5_best_pl3, route_5_best = self.get_best_pls(
            full_routes[7],
            7,
            index_by_route_pl
        )
        best_pls.append([route_5_best_pl1, route_5_best_pl2, route_5_best_pl3, route_5_best])

        return best_pls

    @staticmethod
    def get_random_package_size():
        all_package_size_combinations = [
            PackageSize(
                length=0.8,
                width=1.2,
                height=0.8
            ),
            PackageSize(
                length=0.8,
                width=1.2,
                height=0.9
            ),
            PackageSize(
                length=0.8,
                width=1.2,
                height=1
            ),
            PackageSize(
                length=0.8,
                width=1.2,
                height=1.1
            ),
            PackageSize(
                length=1,
                width=1.2,
                height=1
            ),
            PackageSize(
                length=1,
                width=1.2,
                height=1.1
            ),
            PackageSize(
                length=1.1,
                width=1.1,
                height=1
            ),
            PackageSize(
                length=1.1,
                width=1.1,
                height=1.1
            ),
        ]
        return random.choice(all_package_size_combinations)

    def _get_optimal_results_step_response(self, event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )
        step_response.screen_texts = [
            'Выбрать минимальное по стоимотси предложение провайдера и самую оптимальную комбинацию предложений по всем цепям поставок и дать рекомендации по реализации проекта'
        ]

        pl1_result = round(sum([r.best_pls[0].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2)
        pl2_result = round(sum([r.best_pls[1].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2)
        pl3_result = round(sum([r.best_pls[2].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2)
        combo_result = round(sum([r.best_pls[3].value * r.n_40_foot_containers for r in event.source_data.mini_routes]), 2)
        step_response.pl1_formula = f'{pl1_result}: {"-".join([r.best_pls[0].index for r in event.source_data.mini_routes])}'
        step_response.pl2_formula = f'{pl2_result}: {"-".join([r.best_pls[1].index for r in event.source_data.mini_routes])}'
        step_response.pl3_formula = f'{pl3_result}: {"-".join([r.best_pls[2].index for r in event.source_data.mini_routes])}'
        step_response.combo_formula = f'{combo_result}: {"-".join([r.best_pls[3].index for r in event.source_data.mini_routes])}'

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
    def _get_full_routes_with_pls_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = [
            'Рассчитать стоимость доставки для всех маршрутов доставки по ставкам логистических провайдеров']

        pl_routes = []
        counter = 1
        for route in event.source_data.full_routes:
            for i, pl in enumerate(route.three_pls_bets):
                if pl:
                    container_length = 12
                    container_width = 2.33
                    container_height = 2.35
                    number_of_packages_in_container = math.floor(
                        container_length / event.source_data.package_size.length
                        * container_width / event.source_data.package_size.width
                        * container_height / event.source_data.package_size.height,
                    )
                    n_containers = math.ceil(route.weight_in_tons / (
                                number_of_packages_in_container * event.source_data.package_weight_in_ton))
                    pl_routes.append(
                        PLRoute(
                            supply_chain=f"{route.country_from - route.country_to}",
                            route_number=counter,
                            through=f"через {route.through}",
                            provider=f"3PL{i}",
                            containers_num=n_containers,
                            pl_bet=pl,
                            delivery_price_formula=f"{pl} * {n_containers} = {pl * n_containers}",
                        )
                    )
                    counter += 1

        step_response.pl_routes = pl_routes

        return step_response

    @staticmethod
    def _get_risks_step_response(event, route_index: int):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = [
            'Выберите риски для данного маршрута',
            f'Маршрут:\n{" - ".join(event.source_data.full_routes[route_index].points)}'
        ]

        step_response.current_route = event.source_data.full_routes[route_index]
        step_response.risks = [
            PR2Risk(text="Очередь на мапп", code="MAPP_QUEUE"),
            PR2Risk(text="Погодные условия", code="WEATHER_CONDITION"),
            PR2Risk(text="Смещение выхода судов", code="SHIP_EXIT"),
            PR2Risk(text="Ожидание выгрузки поезда", code="TRAIN_WAITING"),
            PR2Risk(text="Перенос рейса", code="FLIGHT_RESCHEDULING"),
            PR2Risk(text='"Завал" контейнера в порту', code="CONTAINER_IN_PORT"),
            PR2Risk(text="Ожидание подвода платформ", code="WAIT_FOR_PLATFORM"),
            PR2Risk(text="Длительная швартовка судна", code="LONG_MOORING"),
            PR2Risk(text="Закрытие границ государства", code="CLOSING_STATE_BORDERS")
        ]
        return step_response

    @staticmethod
    def _get_formed_routes_table_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )
        step_response.screen_texts = ['Сформировать все возможные маршруты доставки в соответствии с '
                                      'предложенными сервисами для каждой цепи поставок'
                                      'с детализацией по пунктам маршрута и транзитных стран']
        step_response.full_routes = event.source_data.full_routes
        return step_response

    @staticmethod
    def _get_map_route_step_response(event, route_index):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = [f'Сформируйте маршрут {event.source_data.mini_routes[route_index].from_country}-'
                                      f'{event.source_data.mini_routes[route_index].to_country}, нажимая '
                                      f'на логистические объекты на карте. Вы можете предварительно изучить объекты,'
                                      f' кликнув по ним.']

        all_point_cities_from_routes = []
        for r in event.source_data.full_routes:
            all_point_cities_from_routes.extend(r.points)

        all_points_codes_to_show = []
        for p in pr2_class_info.all_points:
            if p.city in all_point_cities_from_routes or p.is_fake:
                all_points_codes_to_show.append(p.code)

        all_points_codes_to_show.extend([p.code for p in event.source_data.full_routes[route_index].points])

        step_response.start_point_code= event.source_data.full_routes[route_index].points[0].code
        step_response.end_point_code = event.source_data.full_routes[route_index].points[-1].code
        step_response.route_length = len(event.source_data.full_routes[route_index].points)
        step_response.points_codes_to_show = all_points_codes_to_show
        step_response.right_route_codes = [p.code for p in event.source_data.full_routes[route_index].points]

        return step_response

    @staticmethod
    def _get_containers_number_20_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

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
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        n_of_transport_packages_in_container_40 = math.floor(
            (12 / event.source_data.package_size.length)
            * (2.33 / event.source_data.package_size.width)
            * (2.35 / event.source_data.package_size.height)
        )

        step_response.screen_texts = ['Расчёт необходимого количества 40-футовых контейнеров для каждой цепи продукции']
        step_response.mini_routes = event.source_data.mini_routes
        step_response.package_weight_in_ton = event.source_data.package_weight_in_ton
        step_response.number_of_packages_in_container = n_of_transport_packages_in_container_40

        return step_response

    @staticmethod
    def _get_describe_container_selection(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        n_of_transport_packages_in_container_20 = math.floor(5.9 / event.source_data.package_size.length
                                                             * (2.33 / event.source_data.package_size.width)
                                                             * (2.35 / event.source_data.package_size.height)
                                                             )

        n_of_transport_packages_in_container_40 = math.floor(
            (12 / event.source_data.package_size.length)
            * (2.33 / event.source_data.package_size.width)
            * (2.35 / event.source_data.package_size.height)
        )

        package_volume = round(
            event.source_data.package_size.length * event.source_data.package_size.width * event.source_data.package_size.height,
            2)

        twenty_foot_formulas = [
            FormulaRow(
                name='Погрузочный объём контейнера, куб.м',
                formula='5,9*2,33*2,35=32,3'
            ),
            FormulaRow(
                name=f'Объём транспортного пакета, куб.м',
                formula=f'{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}='
                        f'{round(event.source_data.package_size.length * event.source_data.package_size.width * event.source_data.package_size.height, 2)}',
            ),
            FormulaRow(
                name=f'Количество транспортных пакетов, размещаемых в контейнере',
                formula=f'(5,9/{event.source_data.package_size.length})*'
                        f'(2,33/{event.source_data.package_size.width})*'
                        f'(2,35/{event.source_data.package_size.height})={n_of_transport_packages_in_container_20}'
            ),
            FormulaRow(
                name=f'Коэффициент использования вместимости',
                formula=f'{n_of_transport_packages_in_container_20}*{package_volume}/32,3='
                        f'{round(n_of_transport_packages_in_container_20 * package_volume / 32.3, 2)}'
            ),
            FormulaRow(
                name=f'Коэффициент использования грузоподъёмности',
                formula=f'{n_of_transport_packages_in_container_20}*{event.source_data.package_weight_in_ton}/21.8='
                        f'{round(n_of_transport_packages_in_container_20 * event.source_data.package_weight_in_ton / 21.8, 2)}'
            )
        ]
        twenty_foot_container_result = ContainerResult(
            header='Обоснование эффективности использования 20-футовых контейнеров с учётом максимального использования их вместимости',
            rows=twenty_foot_formulas
        )

        forty_foot_formulas = [
            FormulaRow(
                name='Погрузочный объём контейнера, куб.м',
                formula='12*2,33*2,35=65,7'
            ),
            FormulaRow(
                name=f'Объём транспортного пакета, куб.м',
                formula=f'{event.source_data.package_size.length}*{event.source_data.package_size.width}*{event.source_data.package_size.height}='
                        f'{round(event.source_data.package_size.length * event.source_data.package_size.width * event.source_data.package_size.height, 2)}',
            ),
            FormulaRow(
                name=f'Количество транспортных пакетов, размещаемых в контейнере',
                formula=f'(12/{event.source_data.package_size.length})*'
                        f'(2,33/{event.source_data.package_size.width})*'
                        f'(2,35/{event.source_data.package_size.height})={n_of_transport_packages_in_container_40}'
            ),
            FormulaRow(
                name=f'Коэффициент использования вместимости',
                formula=f'{n_of_transport_packages_in_container_40}*{package_volume}/65,7='
                        f'{round(n_of_transport_packages_in_container_40 * package_volume / 65.7, 2)}'
            ),
            FormulaRow(
                name=f'Коэффициент использования грузоподъёмности',
                formula=f'{n_of_transport_packages_in_container_40}*{event.source_data.package_weight_in_ton}/21.8='
                        f'{round(n_of_transport_packages_in_container_40 * event.source_data.package_weight_in_ton / 26.4, 2)}'
            )
        ]

        forty_foot_container_result = ContainerResult(
            header='Обоснование эффективности использования 40-футовых контейнеров с учётом максимального использования их вместимости',
            rows=forty_foot_formulas
        )

        step_response.containers_results = [twenty_foot_container_result, forty_foot_container_result]

        return step_response

    @staticmethod
    def _get_screen_4_20_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

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

        step_response.loading_volume = round(
            step_response.container_length * step_response.container_width * step_response.container_height, 2
        )

        step_response.package_volume = (
                step_response.package_height * step_response.package_width * step_response.package_height
        )

        step_response.number_of_packages_in_container = math.floor(
            step_response.container_length / step_response.package_length
            * step_response.container_width / step_response.package_width
            * step_response.container_height / step_response.package_height,
        )

        return step_response

    @staticmethod
    def _get_screen_4_40_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

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

        step_response.loading_volume = round(
            step_response.container_length * step_response.container_width * step_response.container_height, 2
        )

        step_response.package_volume = (
                step_response.package_height * step_response.package_width * step_response.package_height
        )

        step_response.number_of_packages_in_container = math.floor(
            step_response.container_length / step_response.package_length
            * step_response.container_width / step_response.package_width
            * step_response.container_height / step_response.package_height,
        )

        return step_response

    @staticmethod
    def _get_screen_3_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = [
            'На основе аналитики рынка ускоренных железнодорожных и интермодальных контейнерных сервисов '
            '"Door to Door", выбраны предложения ставок логистических провайдеров 3PL. Срок доставки по любому из маршрутов не превышает 25 суток, '
            'что устраивает компанию. '
            'Предложенные сервисы осуществляются в 40-футовых контейнерах через следующие пункты',
        ]
        all_point_names = set()
        for r in event.source_data.full_routes:
            for p in r.points:
                all_point_names.add(p.city)
        step_response.screen_texts.append(
            f"Предложенные сервисы осуществляются в 40-футовых контейнерах через следующие пункты (порт, погранпереход, терминал): "
            f"{', '.join(list(all_point_names))}"
        )

        step_response.full_routes = event.source_data.full_routes

        return step_response

    @staticmethod
    def _get_screen_2_step_response(event):
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.screen_texts = [
            'Оптимальные маршруты цепей поставок продукции',
            'На основании изучения рынка и заключённых договоров на поставку продукции сформированы 5 новых цепей поставок продукции ежемесячно'
            'при разных условиях инкотермс:',
            'Продукция предоставляется к перевозке в сформированных на подоннах транспорных пакетах'
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
        step_response = CurrentStepResponse(
            is_finished=event.is_finished,
            current_step=event.current_step
        )

        step_response.legend = event.legend
        step_response.explanation = event.explanation
        step_response.screen_texts = ["Оптимальные маршруты цепей поставок продукции"]

        return step_response

    @staticmethod
    def get_point_by_city_name(city: str) -> PR2Point:
        for point in pr2_class_info.all_points:
            if point.city == city:
                return point
        raise Exception("Точка не найдена")

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
            n_of_transport_packages_in_container_40
    ) -> list[FullRoute]:
        random_start = random.randint(20, 100)

        all_first_mini_route_cases = [[True, False, True], [False, True, True], [True, True, False]]
        all_first_mini_route_cases.append(random.choice(all_first_mini_route_cases))
        random.shuffle(all_first_mini_route_cases)

        all_random_3pls_grouped = []
        for i in range(4):
            pls = []
            for should_be in all_first_mini_route_cases[i]:
                if should_be:
                    random_pl = random.randint(random_start, random_start + 10) * 100
                    while random_pl in pls:
                        random_pl = random.randint(random_start, random_start + 10) * 100
                    pls.append(random_pl)
                else:
                    pls.append(None)
            all_random_3pls_grouped.append(pls)
        for i in range(4):
            pls = []
            for i in range(3):
                random_pl = random.randint(random_start, random_start + 10) * 100
                while random_pl in pls:
                    random_pl = random.randint(random_start, random_start + 10) * 100
                pls.append(random_pl)
            all_random_3pls_grouped.append(pls)

        n_40_foot_containers = math.ceil(routes_tons[0] / (n_of_transport_packages_in_container_40 * package_weight_in_ton))
        china_route_1 = FullRoute(
            through="Россию",
            country_from="Китай",
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name('Забайкальск'),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china)
            ],
            three_pls_bets=all_random_3pls_grouped[0],
            n_40_foot_containers=n_40_foot_containers
        )

        china_route_2 = FullRoute(
            through="Монголию",
            country_from="Китай",
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name('Наушки'),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china)
            ],
            three_pls_bets=all_random_3pls_grouped[1],
            n_40_foot_containers=n_40_foot_containers
        )

        china_route_3 = FullRoute(
            through="Казахстан",
            country_from="Китай",
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name(chosen_dynamic_border),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china)
            ],
            three_pls_bets=all_random_3pls_grouped[2],
            n_40_foot_containers=n_40_foot_containers
        )

        china_route_4 = FullRoute(
            through="морской торговый порт  (МТП) России",
            country_from="Китай",
            country_to=random_destination_country_for_china,
            weight_in_tons=routes_tons[0],
            points=[
                self.get_point_by_city_name(random_city_from_for_china),
                self.get_point_by_city_name(random_china_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_city_for_china)
            ],
            three_pls_bets=all_random_3pls_grouped[3],
            n_40_foot_containers=n_40_foot_containers
        )

        n_40_foot_containers = math.ceil(
            routes_tons[1] / (n_of_transport_packages_in_container_40 * package_weight_in_ton))
        japan_route_1 = FullRoute(
            through="через МТП России",
            country_from="Япония",
            country_to=random_destination_countries_for_japan[0],
            weight_in_tons=routes_tons[1],
            points=[
                self.get_point_by_city_name(random_city_from_for_japan),
                self.get_point_by_city_name(random_japan_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_japan[0])
            ],
            three_pls_bets=all_random_3pls_grouped[4],
            n_40_foot_containers=n_40_foot_containers
        )

        n_40_foot_containers = math.ceil(
            routes_tons[2] / (n_of_transport_packages_in_container_40 * package_weight_in_ton))
        japan_route_2 = FullRoute(
            through="через МТП России",
            country_from="Япония",
            country_to=random_destination_countries_for_japan[1],
            weight_in_tons=routes_tons[2],
            points=[
                self.get_point_by_city_name(random_city_from_for_japan),
                self.get_point_by_city_name(random_japan_port),
                self.get_point_by_city_name(random_russia_port),
                self.get_point_by_city_name('Брест'),
                self.get_point_by_city_name(random_destination_cities_for_japan[1])
            ],
            three_pls_bets=all_random_3pls_grouped[5],
            n_40_foot_containers=n_40_foot_containers
        )

        n_40_foot_containers = math.ceil(
            routes_tons[3] / (n_of_transport_packages_in_container_40 * package_weight_in_ton))
        south_korea_route_1 = FullRoute(
            through="через МТП России",
            country_from="Южная Корея",
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
            n_40_foot_containers=n_40_foot_containers
        )

        n_40_foot_containers = math.ceil(
            routes_tons[4] / (n_of_transport_packages_in_container_40 * package_weight_in_ton))
        south_korea_route_2 = FullRoute(
            through="через МТП России",
            country_from="Южная Корея",
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
            n_40_foot_containers=n_40_foot_containers
        )

        return [
            china_route_1,
            china_route_2,
            china_route_3,
            china_route_4,
            japan_route_1,
            japan_route_2,
            south_korea_route_1,
            south_korea_route_2
        ]