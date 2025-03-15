import random
from copy import deepcopy
from datetime import datetime
from typing import (
    Optional,
    Type,
    Union,
)

from bson import ObjectId
from fastapi import (
    HTTPException,
    status,
)

from constants.pr1_control_info import pr1_control_info
from constants.practice_one_info import practice_one_info
from db.mongo import (
    CollectionNames,
    get_db,
)
from schemas import (
    CheckpointData,
    CheckpointResponse,
    CheckpointResponseStatus,
    CorrectOrError,
    CurrentStepResponse,
    EventInfo,
    EventStepResult,
    Incoterm,
    PR1ControlEvent,
    PR1ControlResults,
    StartEventDto,
    Step,
    StepRole,
    TestCorrectsAndErrors,
    UserHistoryElement,
    UserOut,
    PR1ControlStep1,
    PR1ControlStep3,
    PR1ControlStep2,
    PR1ControlStepVariant,
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

    def create(self, event_dto: StartEventDto) -> Type[EventInfo]:
        current_step = Step(id=1, code=f'PR1_CONTROL_1')

        test_questions = deepcopy(pr1_control_info.test_questions)
        random.shuffle(test_questions)
        test = test_questions[:20]
        for q in test:
            random.shuffle(q.options)
            right_ids = [option.id for option in q.options if option.is_correct]
            q.right_ids = right_ids
            q.multiple_options = bool(len(right_ids) > 1)

        event = PR1ControlEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            users_ids=self.users_ids,
            current_step=current_step,
            test=test,
            step1=PR1ControlStep1.create(),
            step2=PR1ControlStep2.create(),
            step3=PR1ControlStep3.create(),
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
            step_n = event.current_step.code[-1]
            step: PR1ControlStepVariant = getattr(event, f'step{step_n}')
            step_response.right_answer = step.calculate()
            step_response.right_formula = 'Надо?'
            step_response.right_formula_with_nums = step.get_formula_with_nums()
            step_response.image_name = {'1': 'OIL', '2': 'SHOES', '3': 'TV'}[step_n]
            step_response.incoterm = step.incoterm

            step_response.legend = step.get_formatted_legend()
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
                event.finished_at = datetime.now()
                event.results = self.get_results(event)

                history_element = UserHistoryElement(
                    id=event.id,
                    type=event.event_type,
                    mode=event.event_mode,
                    created_at=event.created_at,
                    finished_at=event.finished_at,
                )

                incoterms = {
                    event.steps_results[0].incoterm: CorrectOrError.CORRECT,
                    event.steps_results[1].incoterm: CorrectOrError.CORRECT,
                    event.steps_results[2].incoterm: CorrectOrError.CORRECT,
                }
                for step in event.steps_results[:3]:
                    if step.fails >= 3:
                        incoterms[step.incoterm] = CorrectOrError.ERROR

                test_results = TestCorrectsAndErrors(correct=0, error=0)
                for step in event.steps_results[3:]:
                    if step.fails > 0:
                        test_results.error += 1
                    else:
                        test_results.correct += 1

                fails_points_mapping = {0: 3, 1: 2, 2: 1, 3: 0}

                incoterm_points_mapping = {
                    event.steps_results[0].incoterm: fails_points_mapping[event.steps_results[0].fails],
                    event.steps_results[1].incoterm: fails_points_mapping[event.steps_results[1].fails],
                    event.steps_results[2].incoterm: fails_points_mapping[event.steps_results[2].fails],
                }

                history_element.incoterm_points_mapping = incoterm_points_mapping

                history_element.test = test_results

                points = test_results.correct
                for num in incoterm_points_mapping.values():
                    points += num

                history_element.points = points

                self.db[CollectionNames.USERS.value].update_one(
                    {'_id': ObjectId(event.users_ids[0])}, {'$push': {'history': history_element.dict()}}
                )
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
            step_n = event.current_step.code[-1]
            step: PR1ControlStepVariant = getattr(event, f'step{step_n}')
            right_answer = step.calculate()

            if not event.steps_results or event.steps_results[-1].step_code != event.current_step.code:
                event.steps_results.append(
                    EventStepResult(
                        step_code=event.current_step.code, users_ids=event.users_ids, fails=0, incoterm=step.incoterm
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

                if step_n == '3':
                    next_step = Step(id=4, code='TEST_1', name=f'Тестовый вопрос #1', role=StepRole.ALL)
                else:
                    next_step_n = int(step_n) + 1
                    _next_step: PR1ControlStepVariant = getattr(event, f'step{next_step_n}')
                    next_step = Step(
                        id=next_step_n,
                        code=f'PR1_CONTROL_{next_step_n}',
                        name=f'Условие {_next_step.incoterm}',
                        role=StepRole.ALL,
                    )
                checkpoint_response.next_step = next_step
                event.current_step = next_step

        checkpoint_response.fails = event.steps_results[-1].fails

        self.db[CollectionNames.EVENTS.value].update_one({'_id': ObjectId(event.id)}, {'$set': event.dict()})

        return checkpoint_response
