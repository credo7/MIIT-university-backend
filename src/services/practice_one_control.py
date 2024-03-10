from typing import Optional
import random

from constants.practice_one_info import practice_one_info
from db.mongo import get_db
from schemas import Incoterm, PR1ControlInput, PR1ControlInputVariables


class PracticeOneControl:
    def __init__(self, users_ids: list[str], computer_id: Optional[int] = None):
        self.computer_id = computer_id
        self.users_ids = users_ids
        self.db = get_db()

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

        exam_input = PR1ControlInput(
            to_point=to_point,  # Откуда берем точку? Формат точки
            from_point=from_point,  # Откуда берем точку? Формат точки
            product_name=product_name,
            variables=PR1ControlInputVariables(
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

        # answers = {}
        # for incoterm in incoterms:
        #     result = self.calculate_incoterm(exam_input, incoterm)
        #     answers[incoterm] = result
        #
        # return PracticeOneExamVariant(
        #     lesson_id=self.lesson.id,
        #     computer_id=self.computer_id,
        #     users_ids=self.users_ids,
        #     event_type=self.lesson.event_type,
        #     event_mode=self.lesson.event_mode,
        #     answers=answers,
        #     exam_input=exam_input,
        # )

    # @staticmethod
    # def calculate_incoterm(exam_input: ExamInputPR1, incoterm: Incoterm):
    #     answer = None
    #
    #     if incoterm == Incoterm.EXW:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #             ]
    #         )
    #     elif incoterm == Incoterm.FCA:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.main_delivery,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #             ]
    #         )
    #     elif incoterm == Incoterm.FOB:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.unloading_during_transport,
    #                 exam_input.variables.delivery_to_port,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.loading_on_board,
    #             ]
    #         )
    #     elif incoterm == Incoterm.FAS:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.unloading_during_transport,
    #                 exam_input.variables.delivery_to_port,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #             ]
    #         )
    #     elif incoterm == Incoterm.CFR:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.unloading_during_transport,
    #                 exam_input.variables.delivery_to_port,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.loading_on_board,
    #                 exam_input.variables.transport_to_destination,
    #             ]
    #         )
    #     elif incoterm == Incoterm.CIP:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.delivery_to_carrier,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.transport_to_destination,
    #                 exam_input.variables.insurance,
    #             ]
    #         )
    #     elif incoterm == Incoterm.CPT:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.delivery_to_carrier,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.transport_to_destination,
    #             ]
    #         )
    #     elif incoterm == Incoterm.CIF:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.unloading_during_transport,
    #                 exam_input.variables.delivery_to_port,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.loading_on_board,
    #                 exam_input.variables.transport_to_destination,
    #                 exam_input.variables.insurance,
    #             ]
    #         )
    #     elif incoterm == Incoterm.DDP:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.delivery_to_carrier,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.unloading_seller_agreement,
    #                 exam_input.variables.import_customs_formalities_and_payments,
    #             ]
    #         )
    #     elif incoterm == Incoterm.DAP:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.delivery_to_carrier,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.transport_to_destination,
    #                 exam_input.variables.unloading_seller_agreement,
    #             ]
    #         )
    #     elif incoterm == Incoterm.DPU:
    #         answer = sum(
    #             [
    #                 exam_input.variables.product_price,
    #                 exam_input.variables.packaging,
    #                 exam_input.variables.product_examination,
    #                 exam_input.variables.loading_during_transport,
    #                 exam_input.variables.delivery_to_carrier,
    #                 exam_input.variables.export_customs_formalities_and_payments,
    #                 exam_input.variables.transport_to_terminal,
    #                 exam_input.variables.unloading_on_terminal,
    #             ]
    #         )
    #     return answer