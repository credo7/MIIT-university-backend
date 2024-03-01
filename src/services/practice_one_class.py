import random
from typing import List, Dict, Optional, Type
from bson import ObjectId

from copy import deepcopy
from constants.practice_one_info import practice_one_info
from db.mongo import get_db, CollectionNames
from schemas import (
    PracticeOneBet,
    Logist,
    OptionPR1,
    PracticeOneBetOut,
    TablePR1,
    Incoterm,
    StartEventDto,
    PR1ClassEvent,
    PR1ClassVariables,
    CheckpointData,
    CheckpointResponse,
    EventStepResult,
    CheckpointResponseStatus, PR1ClassResults, UserOut, SubResult, AnswerStatus, EventInfo, ChosenOption,
    PR1ClassBetType, BetsRolePR1, PR1ClassChosenBet, IncotermInfo,
)
from services.utils import normalize_mongo


class PracticeOneClass:
    def __init__(self, users_ids: List[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    def create(self, event_dto: StartEventDto) -> Type[EventInfo]:
        variables = self.prepare_event_variables()

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
            test=variables.test,
            current_step=variables.zero_step,
        )

        event_db = self.db[CollectionNames.EVENTS.value].insert_one(event.dict())

        event_db = self.db[CollectionNames.EVENTS.value].find_one({"_id": event_db.inserted_id})

        return normalize_mongo(event_db, EventInfo)

    @staticmethod
    def _get_next_step(event: PR1ClassEvent, checkpoint_response: CheckpointResponse):
        if checkpoint_response.status in (
            CheckpointResponseStatus.SUCCESS.value,
            CheckpointResponseStatus.FAILED.value,
        ):
            # Если этот чекпоинт завершен, то обновляем current_step
            current_step_index = practice_one_info.steps.index(event.current_step)
            if len(practice_one_info.steps) >= current_step_index + 2:
                return practice_one_info.steps[current_step_index + 1]
            else:
                return 'FINISHED'
        else:
            return event.current_step

    def get_results(self, event: PR1ClassEvent) -> list[PR1ClassResults]:
        results = []

        for user_id in self.users_ids:
            incoterms_results: dict[Incoterm, SubResult] = {}
            test_result = SubResult()

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

                if "TEST" in step.step_code:
                    if user_id in step.users_ids:
                        if step.fails == 0:
                            test_result.correct += 1
                        elif step.fails < 3:
                            test_result.correct_with_fails += 1
                        else:
                            test_result.failed += 1

            user_db = self.db[CollectionNames.USERS.value].find_one({
                "_id": ObjectId(user_id)
            })

            user = normalize_mongo(user_db, UserOut)

            minimal_incoterms = {}
            for incoterm, sub_result in incoterms_results.items():
                if sub_result.failed > 0:
                    minimal_incoterms[incoterm] = AnswerStatus.FAILED.value
                elif sub_result.correct_with_fails > 0:
                    minimal_incoterms[incoterm] = AnswerStatus.CORRECT_WITH_FAILS.value
                else:
                    minimal_incoterms[incoterm] = AnswerStatus.CORRECT.value

            result = PR1ClassResults(
                first_name=user.first_name,
                last_name=user.last_name,
                surname=user.surname,
                user_id=user.id,
                event_type=event.event_type,
                event_mode=event.event_mode,
                event_id=event.id,
                test_result=test_result,
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
                        id=bet.id,
                        name=bet.name,
                        rate=bet.rate,
                        chosen_by=chosen_by,
                        type=bet_type
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
                total=agreement_price_seller + delivery_price_buyer
            )

            incoterms_mapping[incoterm] = incoterm_info

        return incoterms_mapping

    def checkpoint(self, event: PR1ClassEvent, checkpoint_dto: CheckpointData) -> CheckpointResponse:
        checkpoint_response = CheckpointResponse()

        if 'BUYER' in event.current_step.code or 'SELLER' in event.current_step.code:
            incoterm = event.current_step.code[:3]

            if checkpoint_dto.step_code != event.current_step.code:
                raise Exception(f'Backend ждёт {event.current_step.code} step_code')

            required_bets = []
            common_bets = []

            for bet in event.bets:
                if 'SELLER' in event.current_step.code and incoterm in bet.bet_pattern.seller:
                    required_bets.append(bet)
                if 'BUYER' in event.current_step.code and incoterm in bet.bet_pattern.buyer:
                    required_bets.append(bet)
                if incoterm in bet.bet_pattern.common:
                    common_bets.append(bet)

            required_bets_map = {bet.id: bet for bet in required_bets}
            common_bets_map = {bet.id: bet for bet in common_bets}

            # Если покупатель, то он должен довыбрать все общие ставки, если такие остались
            if 'BUYER' in event.current_step.code:
                if incoterm in event.common_bets_ids_chosen_by_seller:
                    for id in event.common_bets_ids_chosen_by_seller[incoterm]:
                        del common_bets_map[id]
                    required_bets_map.update(common_bets_map)

            not_needed_ids = []
            common_bets_ids_chosen_by_buyer = []

            for user_bet_id in checkpoint_dto.answer_ids:
                if user_bet_id in required_bets_map:
                    del required_bets_map[user_bet_id]
                elif user_bet_id in common_bets_map:
                    common_bets_ids_chosen_by_buyer.append(user_bet_id)
                    del common_bets_map[user_bet_id]
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

                new_step_result = EventStepResult(
                    step_code=event.current_step.code, users_ids=users_ids, fails=0, incoterm=incoterm
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

            print(f'\nNEXT_step is = {next_step}\n')

            event.current_step = next_step
            checkpoint_response.next_step = next_step
            checkpoint_response.fails = current_step_result.fails

        elif event.current_step.code in ('SELECT_LOGIST', 'OPTIONS_COMPARISON', 'CONDITIONS_SELECTION', 'DESCRIBE_OPTION'):
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

            if event.current_step.code == 'SELECT_LOGIST':
                event.chosen_logist_index = checkpoint_dto.chosen_index

            if event.current_step.code == 'OPTIONS_COMPARISON':
                pass

            if event.current_step.code == 'CONDITIONS_SELECTION':
                print(f"\nevent.options_comparison={event.options_comparison}\n")
                print(f"\ncheckpoint_dto.chosen_incoterm={checkpoint_dto.chosen_incoterm}\n")
                event.chosen_option = ChosenOption(
                    agreement_price_seller=event.options_comparison[checkpoint_dto.chosen_incoterm].agreement_price_seller,
                    delivery_price_buyer=event.options_comparison[checkpoint_dto.chosen_incoterm].delivery_price_buyer,
                    total=event.options_comparison[checkpoint_dto.chosen_incoterm].total,
                    incoterm=checkpoint_dto.chosen_incoterm.value
                )

            step_result = EventStepResult(
                step_code=event.current_step.code,
                users_ids=event.users_ids,
                fails=0,
                is_finished=True,
                description=checkpoint_dto.text,
            )
            event.steps_results.append(step_result)

            next_step = self._get_next_step(event, checkpoint_response)
            event.current_step = next_step
            checkpoint_response.next_step = next_step
            checkpoint_response.fails = step_result.fails
            checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

        elif 'TEST' in event.current_step.code:
            test_question_index = int(event.current_step.code[5:]) - 1
            required_ids = [option.id for option in event.test[test_question_index].options if option.is_correct]
            not_needed_ids = []

            for id in checkpoint_dto.answer_ids:
                if id in required_ids:
                    required_ids.remove(id)
                else:
                    not_needed_ids.append(id)

            if event.current_step.code != event.steps_results[-1].step_code:
                step_result = EventStepResult(
                    step_code=event.current_step.code, users_ids=event.users_ids, fails=0,
                )
                event.steps_results.append(step_result)

            if required_ids or not_needed_ids:
                event.steps_results[-1].fails += 1
                if event.steps_results[-1].fails == 3:
                    checkpoint_response.status = CheckpointResponseStatus.FAILED.value
                else:
                    checkpoint_response.status = CheckpointResponseStatus.TRY_AGAIN.value
            else:
                event.steps_results[-1].is_finished = True
                checkpoint_response.status = CheckpointResponseStatus.SUCCESS.value

            if required_ids:
                checkpoint_response.missed_ids = required_ids
            if not_needed_ids:
                checkpoint_response.not_needed_ids = not_needed_ids

            next_step = self._get_next_step(event, checkpoint_response)
            event.current_step = next_step
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
        points = ['FROM', 'WHERE']
        product_options = ['PRODUCT_NAME']
        product = random.choice(product_options)
        from_country = points[0]
        to_country = points[1]
        product_price = random.randrange(1000, 9000, 100)
        legend = practice_one_info.legend_pattern.format(product, from_country, to_country, product_price)

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
        test = self.prepare_test()
        zero_step = practice_one_info.steps[0]

        return PR1ClassVariables(
            legend=legend,
            product=product,
            from_country=from_country,
            to_country=to_country,
            product_price=product_price,
            bets=bets,
            logists=logists,
            test=test,
            zero_step=zero_step,
        )

    @staticmethod
    def prepare_logists() -> List[Logist]:
        logists = practice_one_info.logists.copy()
        random.shuffle(logists)
        chosen_logists = logists[:3]
        return [Logist(description=desc) for desc in chosen_logists]

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
    def prepare_test():
        questions = [
            *deepcopy(practice_one_info.classic_test_questions.first_block),
            *deepcopy(practice_one_info.classic_test_questions.second_block),
            *deepcopy(practice_one_info.classic_test_questions.third_block),
        ]

        random.shuffle(questions)

        for question in questions[:20]:
            random.shuffle(question.options)

        return questions[:20]

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
