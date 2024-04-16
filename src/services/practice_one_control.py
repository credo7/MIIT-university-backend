from typing import Optional, Union, Type
import random

from fastapi import HTTPException, status
from bson import ObjectId

from constants.pr1_control_info import pr1_control_info
from constants.practice_one_info import practice_one_info
from db.mongo import get_db, CollectionNames
from schemas import (
    Incoterm,
    PR1ControlEvent,
    CurrentStepResponse,
    CheckpointResponse,
    CheckpointData,
    EventStepResult,
    CheckpointResponseStatus,
    Step,
    StepRole,
    StartEventDto,
    EventInfo,
    PR1ControlResults,
    UserOut,
)
from services.utils import normalize_mongo


class PracticeOneControl:
    def __init__(self, users_ids: list[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    def get_results(self, event: PR1ControlEvent):
        incoterms_results = {}
        right_tests = 0

        for step in event.steps_results:
            if step.incoterm:
                if step.fails:
                    points = 0
                else:
                    points = 3
                if step.incoterm in incoterms_results:
                    incoterms_results[step.incoterm] += points
                else:
                    incoterms_results[step.incoterm] = points
            else:
                if not step.fails:
                    right_tests += 1

        user_db = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(event.users_ids[0])})

        user = normalize_mongo(user_db, UserOut)

        return PR1ControlResults(
            user_id=event.users_ids[0],
            first_name=user.first_name,
            last_name=user.last_name,
            event_type=event.event_type,
            event_mode=event.event_mode,
            surname=user.surname,
            event_id=event.id,
            right_test_answers=right_tests,
            incoterms_points=incoterms_results,
        )

    # def generate_exam(self):
    #     to_point = 'Выборг (Россия)'
    #     from_point = 'Бильбао (Испания)'
    #     product_name = 'оливĸовое масло в бутылĸах'
    #     product_price = 2
    #     total_products = 7500  # TODO: посмотреть насчет всего бут ( чтобы для всего работало )
    #     # морской/наземный транспорт?
    #     loading_during_transport = 100
    #     # loading_work_price = 100 # TODO: что це это такое??
    #     delivery_to_port = 300
    #     loading_on_board = 200
    #     main_delivery = 2000
    #     insurance = 1000
    #     incoterm: Incoterm = Incoterm.FAS
    #
    #     exam_input = PR1ControlInput(
    #         to_point=to_point,  # Откуда берем точку? Формат точки
    #         from_point=from_point,  # Откуда берем точку? Формат точки
    #         product_name=product_name,
    #         variables=PR1ControlInputVariables(
    #             product_price=product_price,  # Что такое стоимость производителя?
    #             total_products=total_products,  # Используется ли при расчетах?
    #             # packaging=,  # ??? Где оно в тексте? Или оно опционально
    #             # product_examination=, # ???  Где оно в тексте? Или оно опционально
    #             loading_during_transport=loading_during_transport,
    #             # unloading_during_transport=0, #???  Где оно в тексте? Или оно опционально
    #             main_delivery=main_delivery,
    #             # export_customs_formalities_and_payments=, # ??? Где оно в тексте? Или оно опционально
    #             delivery_to_port=delivery_to_port,
    #             loading_on_board=loading_on_board,
    #             # transport_to_destination=, # ??? Где оно в тексте? Или оно опционально
    #             # delivery_to_carrier=, # ??? Тоже ли самое, что и delivery_to_port
    #             insurance=insurance,
    #             # unloading_seller_agreement=, # ??? Где оно в тексте? Или оно опционально
    #             # import_customs_formalities_and_payments=, # ??? Где оно в тексте? Или оно опционально
    #             # transport_to_terminal=, # ??? Тоже ли самое, что и delivery_to_carrier
    #             # unloading_on_terminal=, # ???
    #         ),
    #     )

    # Extra questions:
    # Где-то евро за бут., а где-то другое
    # Как понимаем морским транспортом следует или нет
    # Предлагаю делать заготовленные варианты!

    # f"""
    # В {exam_input.to_point} из {exam_input.from_point} поставляется {exam_input.product_name}.
    # Цена товара – {exam_input.variables.product_price} евро за бут., всего {exam_input.variables.total_products} бут.
    # Товар следует морсĸим транспортом.
    # Расходы на погрузку – {exam_input.variables.loading_during_transport} евро.
    # Доставĸа товара в порт отгрузĸи – {exam_input.variables.delivery_to_port} евро.
    # Стоимость погрузĸи на борт судна в порту {exam_input.from_point} составляет {exam_input.variables.loading_on_board} евро.
    # Транспортные расходы из {exam_input.from_point} в {exam_input.to_point} – {exam_input.variables.transport_to_destination} евро.
    # Товар застрахован, расходы на страхование {exam_input.variables.insurance} евро.
    # Сделĸа заĸлючена на условиях поставĸи {0}-порт {exam_input.from_point}.
    # Определить ĸонтраĸтную стоимость.
    # """
    #
    # incoterms = practice_one_info.all_incoterms.copy()
    # random.shuffle(incoterms)
    # incoterms = ['EXW', 'FAS', 'FOB']
    # # incoterms = incoterm[:3]
    #
    # answers = {}
    # for incoterm in incoterms:
    #     result = self.calculate_incoterm(exam_input, incoterm)
    #     answers[incoterm] = result
    #
    # return PR1ControlEvent(
    #     computer_id=self.computer_id,
    #     users_ids=self.users_ids,
    #     answers=answers,
    #     incoterms=incoterms,
    #     exam_input=exam_input,
    # )

    def create(self, event_dto: StartEventDto) -> Type[EventInfo]:
        random_incoterms: list[Incoterm] = list(Incoterm)
        random.shuffle(random_incoterms)
        random_incoterms = random_incoterms[:3]

        first_incoterm = random_incoterms[0]
        # first_incoterm = pr1_control_info.variants[0].incoterms[0]

        current_step = Step(
            id=1, code=f'INCOTERM_{first_incoterm.value}', name=f'Инкотерм {first_incoterm}', role=StepRole.ALL
        )

        random.shuffle(pr1_control_info.variants[0].test_questions)
        test = pr1_control_info.variants[0].test_questions[:20]
        for q in test:
            random.shuffle(q.options)
            right_ids = [option.id for option in q.options if option.is_correct]
            q.right_ids = right_ids
            q.multiple_options = bool(len(right_ids) > 1)

        pr1_control_info.variants[0].incoterms = random_incoterms

        event = PR1ControlEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            users_ids=self.users_ids,
            current_step=current_step,
            test=test,
            **pr1_control_info.variants[0].dict(),
        )

        event_db = self.db[CollectionNames.EVENTS.value].insert_one(event.dict())

        event_db = self.db[CollectionNames.EVENTS.value].find_one({'_id': event_db.inserted_id})

        return normalize_mongo(event_db, EventInfo)

    def get_current_step(self, event: Union[PR1ControlEvent, Type[PR1ControlEvent]]):
        step_response = CurrentStepResponse()
        if event.is_finished:
            step_response.is_finished = True
            return step_response

        step_response.current_step = event.current_step
        if 'TEST' in event.current_step.code:
            test_question_index = int(event.current_step.code[5:]) - 1
            step_response.test_question = event.test[test_question_index]
        else:
            current_incoterm = event.current_step.code[-3:]

            step_response.right_answer = event.calculate_incoterm(current_incoterm)
            step_response.right_formula = event.get_formula(current_incoterm)
            step_response.right_formula_with_nums = event.get_formula_with_nums(current_incoterm)
            step_response.image_name = 'oil'

            step_response.legend = event.legend.format(current_incoterm)
        return step_response

    def checkpoint(self, event: Union[PR1ControlEvent, Type[PR1ControlEvent]], checkpoint_dto: CheckpointData):
        checkpoint_response = CheckpointResponse()

        if checkpoint_dto.step_code != event.current_step.code:
            raise Exception(f'Backend ждёт {event.current_step.code} step_code')

        if 'TEST' in event.current_step.code:
            test_question_index = int(event.current_step.code.split('_')[1]) - 1
            question = event.test[test_question_index]

            required_ids = [option.id for option in question.options if option.is_correct]
            not_needed_ids = []

            for id in checkpoint_dto.answer_ids:
                if id in required_ids:
                    required_ids.remove(id)
                else:
                    not_needed_ids.append(id)

            if event.steps_results[-1].step_code != event.current_step.code:
                event.steps_results.append(
                    EventStepResult(step_code=event.current_step.code, users_ids=event.users_ids, fails=0,)
                )

            if required_ids or not_needed_ids:
                checkpoint_response.not_needed_ids = not_needed_ids
                checkpoint_response.missed_ids = required_ids
                event.steps_results[-1].fails += 1
                checkpoint_response.status = CheckpointResponseStatus.FAILED
            else:
                checkpoint_response.status = CheckpointResponseStatus.SUCCESS

            if test_question_index == 19:
                finished_step = Step(id=-1, code='FINISHED', name=f'Работа завершена', role=StepRole.ALL)
                checkpoint_response.next_step = finished_step
                event.current_step = finished_step
                event.is_finished = True
            else:
                next_step = Step(
                    id=3 + test_question_index + 2,
                    code=f'TEST_{test_question_index+2}',
                    name=f'Тестовый вопрос #{test_question_index+2}',
                    role=StepRole.ALL,
                )
                checkpoint_response.next_step = next_step
                event.current_step = next_step
        else:
            current_incoterm = event.current_step.code.split('_')[1]
            right_answer = event.calculate_incoterm(current_incoterm)

            if not event.steps_results or event.steps_results[-1].step_code != event.current_step.code:
                event.steps_results.append(
                    EventStepResult(
                        step_code=event.current_step.code, users_ids=event.users_ids, fails=0, incoterm=current_incoterm
                    )
                )

            try:
                user_answer = eval(checkpoint_dto.formula)
            except:
                user_answer = None

            if user_answer == right_answer:
                checkpoint_response.status = CheckpointResponseStatus.SUCCESS
                event.steps_results[-1].is_finished = True
            else:
                event.steps_results[-1].fails += 1

                if event.steps_results[-1].fails < 3:
                    checkpoint_response.status = CheckpointResponseStatus.TRY_AGAIN
                else:
                    checkpoint_response.status = CheckpointResponseStatus.FAILED

            if checkpoint_response.status not in (CheckpointResponseStatus.SUCCESS, CheckpointResponseStatus.FAILED):
                checkpoint_response.next_step = event.current_step
            else:
                incoterm_index = 0
                for i, incoterm in enumerate(event.incoterms):
                    if incoterm.value == current_incoterm:
                        incoterm_index = i
                        break

                if incoterm_index == 2:
                    next_step = Step(id=4, code='TEST_1', name=f'Тестовый вопрос #1', role=StepRole.ALL)
                else:
                    next_step = Step(
                        id=incoterm_index + 2,
                        code=f'INCOTERM_{event.incoterms[incoterm_index+1].value}',
                        name=f'Условие {event.incoterms[incoterm_index+1].value}',
                        role=StepRole.ALL,
                    )
                checkpoint_response.next_step = next_step
                event.current_step = next_step

        checkpoint_response.fails = event.steps_results[-1].fails

        self.db[CollectionNames.EVENTS.value].update_one({'_id': ObjectId(event.id)}, {'$set': event.dict()})

        return checkpoint_response
