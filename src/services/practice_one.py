import random
from typing import List, Dict

from pymongo.database import Database

from constants.practice_one_info import practice_one_info
from db.mongo import get_db, CollectionNames
from schemas import (
    PracticeOneBet,
    PracticeOneVariables,
    Logist,
    OptionPR1,
    PracticeOneVariant,
    PracticeOneBetOut,
    TablePR1,
    Lesson,
    Incoterm,
    ExamInputPR1,
    ExamInputVariablesPR1,
    PracticeOneExamVariant, StartEventDto, PR1ClassEvent, PR1ClassVariables,
)


class PracticeOne:
    def __init__(self, computer_id: int, users_ids: List[str]):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

    def create_pr1_class(self, event_dto: StartEventDto):
        variables = self.prepare_event_variables()
        logists = self.prepare_logists()

        event = PR1ClassEvent(
            computer_id=self.computer_id,
            event_type=event_dto.type,
            event_mode=event_dto.mode,
            logists=logists,
            users_ids=self.users_ids,
            legend=variables.legend,
            product=variables.product,
            from_country=variables.from_country,
            to_country=variables.to_country,
            product_price=variables.product_price,
        )

        self.db[CollectionNames.EVENTS.value].insert_one(event.dict())


    def generate_classic(self) -> PracticeOneVariant:
        input_variables = self.prepare_event_variables()

        tables = self.prepare_tables(input_variables)
        logists = self.prepare_logists()
        options = self.prepare_options(tables=tables, product_price=input_variables.product_price)
        tests = self.prepare_tests_class()

        return PracticeOneVariant(
            lesson_id=self.lesson.id,
            computer_id=self.computer_id,
            event_type=self.lesson.event_type,
            event_mode=self.lesson.event_mode,
            legend=input_variables.legend,
            product=input_variables.product,
            from_country=input_variables.from_country,
            to_country=input_variables.to_country,
            product_price=input_variables.product_price,
            tables=tables,
            logists=logists,
            options=options,
            tests=tests,
            users_ids=self.users_ids,
        )

    def generate_exam(self):
        to_point = 'Выборг (Россия)'
        from_point = 'Бильбао (Испания)'
        product_name = 'оливĸовое масло в бутылĸах'
        product_price = 2
        total_products = 7500  # TODO: посмотреть насчет всего бут ( чтобы для всего работало )
        # морской/наземный транспорт?
        loading_during_transport = 100
        # loading_work_price = 100 # TODO: что це это такое??
        delivery_to_port = 300
        loading_on_board = 200
        main_delivery = 2000
        insurance = 1000
        incoterm: Incoterm = Incoterm.FAS

        exam_input = ExamInputPR1(
            to_point=to_point,  # Откуда берем точку? Формат точки
            from_point=from_point,  # Откуда берем точку? Формат точки
            product_name=product_name,
            variables=ExamInputVariablesPR1(
                product_price=product_price,  # Что такое стоимость производителя?
                total_products=total_products,  # Используется ли при расчетах?
                # packaging=,  # ??? Где оно в тексте? Или оно опционально
                # product_examination=, # ???  Где оно в тексте? Или оно опционально
                loading_during_transport=loading_during_transport,
                # unloading_during_transport=0, #???  Где оно в тексте? Или оно опционально
                main_delivery=main_delivery,
                # export_customs_formalities_and_payments=, # ??? Где оно в тексте? Или оно опционально
                delivery_to_port=delivery_to_port,
                loading_on_board=loading_on_board,
                # transport_to_destination=, # ??? Где оно в тексте? Или оно опционально
                # delivery_to_carrier=, # ??? Тоже ли самое, что и delivery_to_port
                insurance=insurance,
                # unloading_seller_agreement=, # ??? Где оно в тексте? Или оно опционально
                # import_customs_formalities_and_payments=, # ??? Где оно в тексте? Или оно опционально
                # transport_to_terminal=, # ??? Тоже ли самое, что и delivery_to_carrier
                # unloading_on_terminal=, # ???
            ),
        )

        # Extra questions:
        # Где-то евро за бут., а где-то другое
        # Как понимаем морским транспортом следует или нет
        # Предлагаю делать заготовленные варианты!

        f"""
        В {exam_input.to_point} из {exam_input.from_point} поставляется {exam_input.product_name}. 
        Цена товара – {exam_input.variables.product_price} евро за бут., всего {exam_input.variables.total_products} бут. 
        Товар следует морсĸим транспортом.
        Расходы на погрузку – {exam_input.variables.loading_during_transport} евро. 
        Доставĸа товара в порт отгрузĸи – {exam_input.variables.delivery_to_port} евро.
        Стоимость погрузĸи на борт судна в порту {exam_input.from_point} составляет {exam_input.variables.loading_on_board} евро.
        Транспортные расходы из {exam_input.from_point} в {exam_input.to_point} – {exam_input.variables.transport_to_destination} евро. 
        Товар застрахован, расходы на страхование {exam_input.variables.insurance} евро. 
        Сделĸа заĸлючена на условиях поставĸи {0}-порт {exam_input.from_point}. 
        Определить ĸонтраĸтную стоимость.
        """

        incoterms = practice_one_info.all_incoterms.copy()
        random.shuffle(incoterms)
        incoterms = incoterm[:3]

        answers = {}
        for incoterm in incoterms:
            result = self.calculate_incoterm(exam_input, incoterm)
            answers[incoterm] = result

        return PracticeOneExamVariant(
            lesson_id=self.lesson.id,
            computer_id=self.computer_id,
            users_ids=self.users_ids,
            event_type=self.lesson.event_type,
            event_mode=self.lesson.event_mode,
            answers=answers,
            exam_input=exam_input,
        )

    @staticmethod
    def prepare_tables(input: PracticeOneVariables) -> Dict[str, List[TablePR1]]:
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
    def prepare_event_variables(self) -> PracticeOneVariables:
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
            bet = PracticeOneBet(name=bet_pattern.name, rate=rate, bet_pattern=bet_pattern.incoterms)
            bets.append(bet)

        logists = self.prepare_logists()

        return PR1ClassVariables(
            legend=legend,
            product=product,
            from_country=from_country,
            to_country=to_country,
            product_price=product_price,
            bets=bets,
            logists=logists
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
        for i in range(len(tables["BUYER"])):
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
    def prepare_tests_class():
        test_questions = []
        for i in range(3):
            # Первый вопрос
            first_block_questions = practice_one_info.classic_test_questions.first_block.copy()
            first_block_question = first_block_questions[0]
            while first_block_question in test_questions:
                random.shuffle(first_block_questions)
                first_block_question = first_block_questions[0]
            test_questions.append(first_block_question)

            # Второй вопрос
            second_block_questions = practice_one_info.classic_test_questions.second_block.copy()
            second_block_question = second_block_questions[0]
            while second_block_question in test_questions:
                random.shuffle(second_block_questions)
                second_block_question = second_block_questions[0]
            random.shuffle(second_block_question.options)
            test_questions.append(second_block_question)

            # 3-10 вопросы ( по инкотермам ). 8 вопросов
            third_block = []
            for _ in range(8):
                third_block_questions = practice_one_info.classic_test_questions.third_block.copy()
                third_block_question = third_block_questions[0]
                while third_block_question in test_questions:
                    random.shuffle(third_block_questions)
                    third_block_question = third_block_questions[0]
                    random.shuffle(third_block_question.options)
                test_questions.append(third_block_question)

        return [test_questions[0:10], test_questions[10:20], test_questions[20:30]]

    @staticmethod
    def calculate_incoterm(exam_input: ExamInputPR1, incoterm: Incoterm):
        answer = None

        if incoterm == Incoterm.EXW:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                ]
            )
        elif incoterm == Incoterm.FCA:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.main_delivery,
                    exam_input.variables.export_customs_formalities_and_payments,
                ]
            )
        elif incoterm == Incoterm.FOB:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.unloading_during_transport,
                    exam_input.variables.delivery_to_port,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.loading_on_board,
                ]
            )
        elif incoterm == Incoterm.FAS:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.unloading_during_transport,
                    exam_input.variables.delivery_to_port,
                    exam_input.variables.export_customs_formalities_and_payments,
                ]
            )
        elif incoterm == Incoterm.CFR:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.unloading_during_transport,
                    exam_input.variables.delivery_to_port,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.loading_on_board,
                    exam_input.variables.transport_to_destination,
                ]
            )
        elif incoterm == Incoterm.CIP:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.delivery_to_carrier,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.transport_to_destination,
                    exam_input.variables.insurance,
                ]
            )
        elif incoterm == Incoterm.CPT:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.delivery_to_carrier,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.transport_to_destination,
                ]
            )
        elif incoterm == Incoterm.CIF:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.unloading_during_transport,
                    exam_input.variables.delivery_to_port,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.loading_on_board,
                    exam_input.variables.transport_to_destination,
                    exam_input.variables.insurance,
                ]
            )
        elif incoterm == Incoterm.DDP:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.delivery_to_carrier,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.unloading_seller_agreement,
                    exam_input.variables.import_customs_formalities_and_payments,
                ]
            )
        elif incoterm == Incoterm.DAP:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.delivery_to_carrier,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.transport_to_destination,
                    exam_input.variables.unloading_seller_agreement,
                ]
            )
        elif incoterm == Incoterm.DPU:
            answer = sum(
                [
                    exam_input.variables.product_price,
                    exam_input.variables.packaging,
                    exam_input.variables.product_examination,
                    exam_input.variables.loading_during_transport,
                    exam_input.variables.delivery_to_carrier,
                    exam_input.variables.export_customs_formalities_and_payments,
                    exam_input.variables.transport_to_terminal,
                    exam_input.variables.unloading_on_terminal,
                ]
            )
        return answer