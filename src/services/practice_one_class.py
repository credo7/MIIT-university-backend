import copy
import random
from copy import deepcopy
from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
    Type,
    Union,
)

from bson import ObjectId

from constants.practice_one_info import practice_one_info
from db.mongo import (
    CollectionNames,
    get_db,
)
from schemas import (
    AnswerStatus,
    BetsRolePR1,
    CheckpointData,
    CheckpointResponse,
    CheckpointResponseStatus,
    ChosenOption,
    CorrectOrError,
    CurrentStepResponse,
    EventInfo,
    EventStepResult,
    Incoterm,
    IncotermInfo,
    IncotermInfoSummarize,
    Logist,
    OptionPR1,
    PR1ClassBetType,
    PR1ClassChosenBet,
    PR1ClassEvent,
    PR1ClassResults,
    PR1ClassStep,
    PR1ClassVariables,
    PracticeOneBet,
    PracticeOneBetOut,
    StartEventDto,
    Step,
    StepRole,
    SubResult,
    TablePR1,
    TestCorrectsAndErrors,
    UserHistoryElement,
    UserOut,
)
from services.utils import (
    format_with_spaces,
    normalize_mongo,
)


class PracticeOneClass:
    def __init__(self, users_ids: List[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    def create(self, event_dto: StartEventDto) -> Type[EventInfo]:
        variables = self.prepare_event_variables()

        current_step = Step(id=0, code=f'SELECT_LOGIST', name=f'Выбор логиста', role=StepRole.ALL)

        event = PR1ClassEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            logists=variables.logists,
            users_ids=self.users_ids,
            legend=variables.legend,
            product=variables.product,
            from_country=variables.from_country,
            to_country=variables.to_country,
            product_price=variables.product_price,
            bets=variables.bets,
            tests=variables.tests,
            current_step=current_step,
        )

        event_db = self.db[CollectionNames.EVENTS.value].insert_one(event.dict())

        event_db = self.db[CollectionNames.EVENTS.value].find_one({'_id': event_db.inserted_id})

        return normalize_mongo(event_db, EventInfo)

    def continue_work(self, event: Union[PR1ClassEvent, Type[PR1ClassEvent]]):
        if not event.steps_results:
            return

        if 'SELLER' in event.steps_results[-1].step_code:
            event.steps_results.pop()
        if 'BUYER' in event.steps_results[-1].step_code:
            if not event.steps_results[-1].is_finished:
                event.steps_results.pop()
                event.steps_results.pop()

        self.db[CollectionNames.EVENTS.value].update_one(
            {'_id': ObjectId(event.id)}, {'$set': {'steps_results': [sr.dict() for sr in event.steps_results]}}
        )

    def get_current_step(self, pr1_class_event: Union[PR1ClassEvent, Type[PR1ClassEvent]]):
        current_step_response = CurrentStepResponse(current_step=pr1_class_event.current_step,)

        if pr1_class_event.is_finished and 'TEST' not in pr1_class_event.current_step.code:
            current_step_response.is_finished = True
            return current_step_response

        if pr1_class_event.current_step.code == 'OPTIONS_COMPARISON':
            options_comparison = self.get_options_comparison(pr1_class_event)
            pr1_class_event.options_comparison = options_comparison
            self.db[CollectionNames.EVENTS.value].update_one(
                {'_id': ObjectId(pr1_class_event.id)},
                {'$set': {'options_comparison': {key: value.dict() for key, value in options_comparison.items()}}},
            )
            current_step_response.options_comparison = options_comparison
        elif pr1_class_event.current_step.code == 'CONDITIONS_SELECTION':
            current_step_response.delivery_options = {
                key: IncotermInfoSummarize(
                    agreement_price_seller=option.agreement_price_seller,
                    delivery_price_buyer=option.delivery_price_buyer,
                    total=option.total,
                ).dict()
                for key, option in pr1_class_event.options_comparison.items()
            }
        elif 'BUYER' in pr1_class_event.current_step.code or 'SELLER' in pr1_class_event.current_step.code:
            current_step_response.product = pr1_class_event.product
            current_step_response.from_country = pr1_class_event.from_country
            current_step_response.to_country = pr1_class_event.to_country
            current_step_response.product_price = pr1_class_event.product_price

            current_step_response.bets = pr1_class_event.bets
        elif pr1_class_event.current_step.code == 'SELECT_LOGIST':
            current_step_response.logists = pr1_class_event.logists
        elif 'TEST' in pr1_class_event.current_step.code:
            if pr1_class_event.test_index > 2:
                current_step_response.is_finished = True
            index = int(pr1_class_event.current_step.code[5:]) - 1
            current_step_response.test_question = pr1_class_event.tests[pr1_class_event.test_index][index]
        return current_step_response

    @staticmethod
    def _get_next_step(event: PR1ClassEvent, checkpoint_response: CheckpointResponse):
        finished_step = Step(id=-1, code='FINISHED', name=f'Работа завершена', role=StepRole.ALL)
        if checkpoint_response.status in (
            CheckpointResponseStatus.SUCCESS.value,
            CheckpointResponseStatus.FAILED.value,
        ):
            if 'TEST' in event.current_step.code or event.current_step.code == 'DESCRIBE_OPTION':
                if len(event.test_results[event.test_index]) == 20:
                    return finished_step
                else:
                    return Step(
                        id=len(practice_one_info.steps) + len(event.test_results[event.test_index]),
                        code=f'TEST_{len(event.test_results[event.test_index])+1}',
                        name=f'Тестовый вопрос №{len(event.test_results[event.test_index])+1}',
                        role=StepRole.ALL,
                    )

            print(f'steps={practice_one_info.steps[0]}')
            print(f'current_step={event.current_step}')

            # Если этот чекпоинт завершен, то обновляем current_step
            current_step_index = None
            for index, step in enumerate(practice_one_info.steps):
                if step.code == event.current_step.code:
                    current_step_index = index
                    break

            print(f'current_step_index={current_step_index}')

            # current_step_index = practice_one_info.steps.index(event.current_step)
            if len(practice_one_info.steps) >= current_step_index + 2:
                return practice_one_info.steps[current_step_index + 1]
            else:
                return finished_step
        else:
            return event.current_step

    def get_results(self, event: PR1ClassEvent) -> list[PR1ClassResults]:
        results = []

        for user_id in self.users_ids:
            incoterms_results: dict[Incoterm, SubResult] = {}

            for step in event.steps_results:
                if step.incoterm:
                    if user_id in step.users_ids:
                        if step.incoterm not in incoterms_results:
                            incoterms_results[step.incoterm] = SubResult()
                        if step.fails == 0:
                            incoterms_results[step.incoterm].correct += 1
                        elif step.fails < 3:
                            incoterms_results[step.incoterm].correct_with_fails += 1
                        else:
                            incoterms_results[step.incoterm].failed += 1

            final_test_results = [SubResult(), SubResult(), SubResult()]
            for index, test_result in enumerate(event.test_results):
                if not test_result or '20' not in test_result[-1].step_code:
                    break
                for step in test_result:
                    if not step.fails:
                        final_test_results[step.test_index].correct += 1
                    else:
                        final_test_results[step.test_index].failed += 1

            user_db = self.db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user_id)})

            user = normalize_mongo(user_db, UserOut)

            minimal_incoterms = {}
            for incoterm, sub_result in incoterms_results.items():
                if sub_result.failed > 0:
                    minimal_incoterms[incoterm] = AnswerStatus.FAILED.value
                elif sub_result.correct_with_fails > 0:
                    minimal_incoterms[incoterm] = AnswerStatus.CORRECT_WITH_FAILS.value
                else:
                    minimal_incoterms[incoterm] = AnswerStatus.CORRECT.value

            index_of_the_best = 0
            max_corrects = 0
            for index, test_result in enumerate(final_test_results):
                if test_result.correct > max_corrects:
                    index_of_the_best = index
                    max_corrects = test_result.correct

            last_test_index = (
                event.test_index
                if event.test_results[event.test_index] and '20' in event.test_results[event.test_index][-1]
                else event.test_index - 1
            )

            result = PR1ClassResults(
                first_name=user.first_name,
                last_name=user.last_name,
                surname=user.surname,
                user_id=user.id,
                event_type=event.event_type,
                event_mode=event.event_mode,
                event_id=event.id,
                test_results=final_test_results,
                best_test_result=final_test_results[index_of_the_best],
                last_test_result=final_test_results[last_test_index],
                incoterms_results=incoterms_results,
                minimal_incoterms=minimal_incoterms,
            )

            results.append(result)

        return results

    def get_options_comparison(self, pr1_class_event) -> dict[Incoterm, IncotermInfo]:
        incoterms_mapping = {}
        for incoterm in list(Incoterm):
            chosen_bets = []
            for bet in pr1_class_event.bets:
                chosen_by = None
                bet_type = None

                if incoterm in bet.bet_pattern.buyer:
                    bet_type = PR1ClassBetType.BUYER.value
                    chosen_by = BetsRolePR1.BUYER.value
                elif incoterm in bet.bet_pattern.seller:
                    bet_type = PR1ClassBetType.SELLER.value
                    chosen_by = BetsRolePR1.SELLER.value
                elif incoterm in bet.bet_pattern.common:
                    bet_type = PR1ClassBetType.COMMON.value
                    if incoterm in pr1_class_event.common_bets_ids_chosen_by_seller:
                        if bet.id in pr1_class_event.common_bets_ids_chosen_by_seller[incoterm]:
                            chosen_by = BetsRolePR1.SELLER.value
                        else:
                            chosen_by = BetsRolePR1.BUYER.value
                    else:
                        chosen_by = BetsRolePR1.BUYER.value
                if chosen_by is not None or bet_type is not None:
                    chosen_bet = PR1ClassChosenBet(
                        id=bet.id, name=bet.name, rate=bet.rate, chosen_by=chosen_by, type=bet_type
                    )

                    chosen_bets.append(chosen_bet)

            agreement_price_seller = pr1_class_event.product_price
            delivery_price_buyer = 0

            for bet in chosen_bets:
                if bet.chosen_by == BetsRolePR1.BUYER.value:
                    delivery_price_buyer += bet.rate
                else:
                    agreement_price_seller += bet.rate

            incoterm_info = IncotermInfo(
                bets=chosen_bets,
                agreement_price_seller=agreement_price_seller,
                delivery_price_buyer=delivery_price_buyer,
                total=agreement_price_seller + delivery_price_buyer,
            )

            incoterms_mapping[incoterm] = incoterm_info

        return incoterms_mapping

    def checkpoint(
        self, event: Union[PR1ClassEvent, Type[PR1ClassEvent]], checkpoint_dto: CheckpointData
    ) -> CheckpointResponse:
        checkpoint_response = CheckpointResponse()

        if checkpoint_dto.step_code != event.current_step.code:
            raise Exception(f'Backend ждёт {event.current_step.code} step_code')

        if 'BUYER' in event.current_step.code or 'SELLER' in event.current_step.code:
            incoterm = event.current_step.code[:3]

            required_bets = []
            common_bets = []

            for bet in event.bets:
                if 'SELLER' in event.current_step.code and incoterm in bet.bet_pattern.seller:
                    required_bets.append(bet)
                if 'BUYER' in event.current_step.code and incoterm in bet.bet_pattern.buyer:
                    required_bets.append(bet)
                # if incoterm in bet.bet_pattern.common:
                #     common_bets.append(bet)

            required_bets_map = {bet.id: bet for bet in required_bets}
            # common_bets_map = {bet.id: bet for bet in common_bets}

            # Если покупатель, то он должен довыбрать все общие ставки, если такие остались
            # if 'BUYER' in event.current_step.code:
            #     if incoterm in event.common_bets_ids_chosen_by_seller:
            #         for id in event.common_bets_ids_chosen_by_seller[incoterm]:
            #             del common_bets_map[int(id)]
            #         required_bets_map.update(common_bets_map)

            required_bets_for_comments = list(required_bets_map.values())
            # common_bets_for_comments = list(common_bets_map.values())

            not_needed_ids = []
            common_bets_ids_chosen_by_buyer = []

            for user_bet_id in checkpoint_dto.answer_ids:
                if user_bet_id in required_bets_map:
                    del required_bets_map[user_bet_id]
                # elif user_bet_id in common_bets_map:
                #     common_bets_ids_chosen_by_buyer.append(user_bet_id)
                #     del common_bets_map[user_bet_id]
                else:
                    not_needed_ids.append(user_bet_id)

            if not_needed_ids or required_bets_map:
                missed_ids = list(required_bets_map.keys())
                if missed_ids:
                    checkpoint_response.missed_ids = missed_ids
                if not_needed_ids:
                    checkpoint_response.not_needed_ids = not_needed_ids

            if event.current_step.role == 'SELLER':
                if not not_needed_ids and not required_bets_map:
                    # Записываем смежные ставки в выбранные только если ответ продавца правильный
                    event.common_bets_ids_chosen_by_seller[incoterm] = common_bets_ids_chosen_by_buyer

            if not event.steps_results or event.steps_results[-1].step_code != event.current_step.code:
                # Если первая попытка этого checkpoint
                users_ids = []
                if event.current_step.role == 'BUYER' and len(event.users_ids) == 2:
                    users_ids.append(event.users_ids[1])
                else:
                    users_ids.append(event.users_ids[0])

                if 'SELLER' in event.current_step.code:
                    comments = f"Обязательные ставки: {[f'{bet.name}: {bet.rate}' for bet in required_bets_for_comments]}\n"  # f"Необязательные ставки: {[f'{bet.name}: {bet.rate}' for bet in common_bets_for_comments]}"
                else:
                    comments = (
                        f"Обязательные ставки: {[f'{bet.name}: {bet.rate}' for bet in required_bets_for_comments]}"
                    )

                new_step_result = EventStepResult(
                    step_code=event.current_step.code,
                    users_ids=users_ids,
                    fails=0,
                    incoterm=incoterm,
                    comments=comments,
                )
                event.steps_results.append(new_step_result)

            current_step_result = event.steps_results[-1]

            if not checkpoint_response.missed_ids and not checkpoint_response.not_needed_ids:
                checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value
                current_step_result.is_finished = True
            else:
                checkpoint_response.status = CheckpointResponseStatus.TRY_AGAIN.value
                current_step_result.fails += 1

            if current_step_result.fails == 3:
                current_step_result.is_finished = True
                checkpoint_response.status = CheckpointResponseStatus.FAILED.value

            next_step = self._get_next_step(event, checkpoint_response)

            event.current_step = next_step
            checkpoint_response.next_step = next_step
            checkpoint_response.fails = current_step_result.fails

        elif event.current_step.code in (
            'SELECT_LOGIST',
            'OPTIONS_COMPARISON',
            'CONDITIONS_SELECTION',
            'DESCRIBE_OPTION',
        ):
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

            comments = ""
            if event.current_step.code == 'SELECT_LOGIST':
                comments = 'Выбираем логиста. Ни на что не влияет в ПО'
                event.chosen_logist_letter = checkpoint_dto.chosen_letter

            elif event.current_step.code == 'OPTIONS_COMPARISON':
                comments = 'Табличка для сравнения инкотермов, ничего не делаем, можно лишь нажать далее'
                pass

            elif event.current_step.code == 'CONDITIONS_SELECTION':
                chosen_option = ChosenOption(
                    agreement_price_seller=event.options_comparison[
                        checkpoint_dto.chosen_incoterm
                    ].agreement_price_seller,
                    delivery_price_buyer=event.options_comparison[checkpoint_dto.chosen_incoterm].delivery_price_buyer,
                    total=event.options_comparison[checkpoint_dto.chosen_incoterm].total,
                    incoterm=checkpoint_dto.chosen_incoterm.value,
                )
                event.chosen_option = chosen_option
                comments = f'Студент выбирает любой вариант ( ни на что не влияет в ПО )'

            elif event.current_step.code == 'DESCRIBE_OPTION':
                comments = 'Пишем обоснование ( не менее 150 символов )'
                pass

            step_result = EventStepResult(
                step_code=event.current_step.code,
                users_ids=event.users_ids,
                fails=0,
                is_finished=True,
                description=checkpoint_dto.text,
                comments=comments,
            )
            event.steps_results.append(step_result)

            next_step = self._get_next_step(event, checkpoint_response)
            event.current_step = next_step
            checkpoint_response.next_step = next_step
            checkpoint_response.fails = step_result.fails
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

        elif 'TEST' in event.current_step.code:
            if event.test_index > 2:
                raise Exception('Тесты можно выполнить не более 3 раз')

            test = event.tests[event.test_index]
            test_question_index = int(event.current_step.code[5:]) - 1
            required_ids = [option.id for option in test[test_question_index].options if option.is_correct]
            not_needed_ids = []

            for id in checkpoint_dto.answer_ids:
                if id in required_ids:
                    required_ids.remove(id)
                else:
                    not_needed_ids.append(id)

            if not event.test_results[event.test_index]:
                event.test_results[event.test_index].append(
                    EventStepResult(
                        step_code=event.current_step.code,
                        users_ids=event.users_ids,
                        fails=0,
                        test_index=event.test_index,
                    )
                )

            if event.current_step.code != event.test_results[event.test_index][-1].step_code:
                step_result = EventStepResult(
                    step_code=event.current_step.code, users_ids=event.users_ids, fails=0, test_index=event.test_index
                )
                event.test_results[event.test_index].append(step_result)

            if required_ids or not_needed_ids:
                event.test_results[event.test_index][-1].fails += 1
                checkpoint_response.status = CheckpointResponseStatus.FAILED.value
            else:
                checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

            event.test_results[event.test_index][-1].is_finished = True

            if required_ids:
                checkpoint_response.missed_ids = required_ids
            if not_needed_ids:
                checkpoint_response.not_needed_ids = not_needed_ids

            next_step = self._get_next_step(event, checkpoint_response)
            event.current_step = next_step
            if next_step.code == 'FINISHED':
                event.is_finished = True
                event.finished_at = datetime.now()
                event.results = self.get_results(event)
                for i, user_id in enumerate(event.users_ids):
                    history_element = UserHistoryElement(
                        id=event.id,
                        type=event.event_type,
                        mode=event.event_mode,
                        created_at=event.created_at,
                        finished_at=event.finished_at,
                    )

                    incoterms = {inc: CorrectOrError.CORRECT for inc in list(Incoterm)}
                    for step in event.steps_results:
                        if step.step_code == 'DESCRIBE_OPTION':
                            history_element.description = step.description
                        if user_id in step.users_ids:
                            if step.fails >= 3:
                                incoterms[step.incoterm] = CorrectOrError.ERROR

                    best = TestCorrectsAndErrors(correct=0, error=20)
                    for test_result in event.test_results:
                        current = TestCorrectsAndErrors(correct=0, error=0)
                        for step in test_result:
                            if step.fails > 0:
                                current.error += 1
                            else:
                                current.correct += 1
                        if current.correct > best.correct:
                            best = copy.deepcopy(current)

                    history_element.incoterms = incoterms
                    history_element.test = best

                    self.db[CollectionNames.USERS.value].update_one(
                        {'_id': ObjectId(user_id)}, {'$push': {'history': history_element.dict()}}
                    )

            checkpoint_response.next_step = next_step

        self.db[CollectionNames.EVENTS.value].update_one({'_id': ObjectId(event.id)}, {'$set': event.dict()})

        return checkpoint_response

    @staticmethod
    def prepare_tables(input: PR1ClassVariables) -> Dict[str, List[TablePR1]]:
        tables = {'BUYER': [], 'SELLER': [], 'COMMON': []}

        for index, incoterm in enumerate(list(Incoterm)):
            for role in ['BUYER', 'SELLER', 'COMMON']:
                table_bets = []

                for bet in input.bets:
                    is_correct = False

                    if role == 'BUYER':
                        if incoterm in bet.bet_pattern.buyer:
                            is_correct = True
                    elif role == 'SELLER':
                        if incoterm in bet.bet_pattern.seller:
                            is_correct = True

                    table_bet = PracticeOneBetOut(name=bet.name, rate=bet.rate, is_correct=is_correct)
                    table_bets.append(table_bet)

                table = TablePR1(index=index, role=role, incoterm=incoterm, bets=table_bets)

                tables[role].append(table)

        # Динамические ставки. Продавец либо покупатель берет эту ставку на себя.
        # Она обязательна и может быть выбрана лишь одним участником сделки
        for index, incoterm in enumerate(list(Incoterm)):
            common_bets = []

            for bet in input.bets:
                if incoterm in bet.bet_pattern.common:
                    common_bet = PracticeOneBetOut(name=bet.name, rate=bet.rate, is_correct=True)
                    common_bets.append(common_bet)

            tables['COMMON'].append(common_bets)

        return tables

    # @staticmethod
    def prepare_event_variables(self) -> PR1ClassVariables:
        points = ['Бильбао (Испания)', 'Выборг (Россия)']
        product_options = ['сетевое оборудование']
        product = random.choice(product_options)
        from_country = points[0]
        to_country = points[1]
        product_price = random.randrange(1000, 9000, 100)
        legend = practice_one_info.legend_pattern.format(
            product, from_country, to_country, format_with_spaces(product_price)
        )

        bets = []
        for bet_pattern in practice_one_info.bets:
            if bet_pattern.value_percentage.min == bet_pattern.value_percentage.max:
                percentage_from_product_price = bet_pattern.value_percentage.min
            else:
                percentage_from_product_price = (
                    random.randrange(bet_pattern.value_percentage.min * 10, bet_pattern.value_percentage.max * 10, 1)
                    / 10
                )
            rate = round(product_price * percentage_from_product_price / 100)
            bet = PracticeOneBet(id=bet_pattern.id, name=bet_pattern.name, rate=rate, bet_pattern=bet_pattern.incoterms)
            bets.append(bet)

        logists = self.prepare_logists()
        tests = self.prepare_tests()
        zero_step = practice_one_info.steps[0]

        return PR1ClassVariables(
            legend=legend,
            product=product,
            from_country=from_country,
            to_country=to_country,
            product_price=product_price,
            bets=bets,
            logists=logists,
            tests=tests,
            zero_step=zero_step,
        )

    @staticmethod
    def prepare_logists() -> List[Logist]:
        logists = practice_one_info.logists.copy()
        random.shuffle(logists)
        return logists[:3]

    @staticmethod
    def prepare_options(tables, product_price):
        options = []
        for i in range(len(tables['BUYER'])):
            seller = product_price
            buyer = 0

            for bet in tables['SELLER'][i].bets:
                if bet.is_correct:
                    seller += bet.rate
            for bet in tables['BUYER'][i].bets:
                if bet.is_correct:
                    buyer += bet.rate

            incoterm = tables['SELLER'][i].incoterm
            total = buyer + seller

            option = OptionPR1(buyer=buyer, seller=seller, total=total, incoterm=incoterm)

            options.append(option)

        return options

    @staticmethod
    def prepare_tests():
        questions = [
            *deepcopy(practice_one_info.classic_test_questions.first_block),
            *deepcopy(practice_one_info.classic_test_questions.second_block),
            *deepcopy(practice_one_info.classic_test_questions.third_block),
        ]

        tests = []
        for i in range(3):
            random.shuffle(questions)
            tests.append(deepcopy(questions[:20]))

        for test in tests:
            for question in test:
                random.shuffle(question.options)
                if len([option for option in question.options if option.is_correct]) > 1:
                    question.multiple_options = True
                question.right_ids = [option.id for option in question.options if option.is_correct]

        return tests

        # Первый вопрос
        # first_block_questions = practice_one_info.classic_test_questions.first_block.copy()
        # first_block_question = first_block_questions[0]
        # while first_block_question in test_questions:
        #     random.shuffle(first_block_questions)
        #     first_block_question = first_block_questions[0]
        # test_questions.append(first_block_question)
        #
        # # Второй вопрос
        # second_block_questions = practice_one_info.classic_test_questions.second_block.copy()
        # second_block_question = second_block_questions[0]
        # while second_block_question in test_questions:
        #     random.shuffle(second_block_questions)
        #     second_block_question = second_block_questions[0]
        # random.shuffle(second_block_question.options)
        # test_questions.append(second_block_question)
        #
        # # 3-10 вопросы ( по инкотермам ). 8 вопросов
        # third_block = []
        # for _ in range(8):
        #     third_block_questions = practice_one_info.classic_test_questions.third_block.copy()
        #     third_block_question = third_block_questions[0]
        #     while third_block_question in test_questions:
        #         random.shuffle(third_block_questions)
        #         third_block_question = third_block_questions[0]
        #         random.shuffle(third_block_question.options)
        #     test_questions.append(third_block_question)
