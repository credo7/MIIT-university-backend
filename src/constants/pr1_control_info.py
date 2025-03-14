from typing import Optional

from pydantic import BaseModel

from schemas import Incoterm, TestQuestionPR1


class PR1ControlVariant(BaseModel):
    legend: str
    product_price: int
    product_quantity: int = 1
    packaging: Optional[int] = 0
    product_check: Optional[int] = 0
    loading_expenses: Optional[int] = 0
    delivery_to_main_carrier: Optional[int] = 0
    export_formalities: Optional[int] = 0
    loading_unloading_to_point: Optional[int] = 0
    delivery_to_unloading_port: Optional[int] = 0
    loading_on_board: Optional[int] = 0
    transport_expenses_to_port: Optional[int] = 0
    products_insurance: Optional[int] = 0
    unloading_on_seller: Optional[int] = 0
    import_formalities: Optional[int] = 0
    unloading_on_terminal: Optional[int] = 0
    incoterms: list[Incoterm]
    test_questions: list[TestQuestionPR1]


class PR1ControlInfo(BaseModel):
    variants: list[PR1ControlVariant] = []


raw_pr1_control_info = {
    'legend': """В Выборг (Россия) из Бильбао (Испания) поставляется оливĸовое масло в бутылĸах. 

Цена товара – 2 евро за бут., всего 7 500 бут. 

Товар следует морсĸим транспортом. 

Расходы на погрузку – 100 евро. 

Доставĸа товара в порт отгрузĸи – 300 евро. 

Стоимость погрузĸи на борт судна в порту Бильбао составляет 200 евро. 

Транспортные расходы из Бильбао в Выборг – 2 000 евро. 

Товар застрахован, расходы на страхование 1 000 евро. 

Сделĸа заĸлючена на условиях поставĸи {0}-порт Бильбао. 

Определить ĸонтраĸтную стоимость.""",
    'test_questions': [
        {
            'id': 1,
            'question': 'InCoTerms (Инкотермс)',
            'options': [
                {'id': 0, 'value': 'Международные торговые термины', 'is_correct': True},
                {'id': 1, 'value': 'Международные коммерческие правила'},
                {'id': 2, 'value': 'Международная торговая терминология'},
                {'id': 3, 'value': 'Международные коммерческие условия поставки'},
            ],
        },
        {
            'id': 2,
            'question': 'Инкотермс определяют',
            'options': [
                {
                    'id': 0,
                    'value': 'Обязанности продавца и покупателя, риск перехода ответственности, ответственность сторон за расходы',
                    'is_correct': True,
                },
                {'id': 1, 'value': 'Обязанности продавца, покупателя, перевозчика'},
                {'id': 2, 'value': 'Обязанности продавца и покупателя, риск перехода ответственности'},
                {'id': 3, 'value': 'Обязанности продавца и покупателя, какая из сторон отвечает за расходы'},
            ],
        },
        {
            'id': 3,
            'question': 'Базисные условия поставки Инкотермс',
            'options': [
                {
                    'id': 0,
                    'value': 'Определяют обязанности покупателя и продавца\nпо доставке товара ',
                    'is_correct': True,
                },
                {
                    'id': 1,
                    'value': 'Устанавливают момент перехода риска повреждения товара или случайной утери',
                    'is_correct': True,
                },
                {
                    'id': 2,
                    'value': 'Описывают обязанности, риски, расходы продавцов\nи покупателей ',
                    'is_correct': True,
                },
                {'id': 3, 'value': 'Формируются на основе практики международной торговли', 'is_correct': True},
                {
                    'id': 4,
                    'value': 'Переиздаются и совершенствуются в зависимости\nот текущей ситуации',
                    'is_correct': True,
                },
            ],
        },
        {
            'id': 4,
            'question': 'Является ли Инкотермс\nс правовой точки зрения обязательным документом?',
            'options': [{'id': 0, 'value': 'Не является', 'is_correct': True}, {'id': 1, 'value': 'Является'}],
        },
        {
            'id': 5,
            'question': 'Что включает в себя Инкотермс 2020?',
            'options': [
                {'id': 0, 'value': '4 группы – 11 терминов ', 'is_correct': True},
                {'id': 1, 'value': '4 группы – 12 терминов'},
                {'id': 2, 'value': '4 группы – 10 терминов'},
                {'id': 3, 'value': '3 группы – 11 терминов'},
            ],
        },
        {
            'id': 6,
            'question': 'Как обозначается условие поставки «Свободно\nс завода»?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'FCA'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'FAS'},
            ],
        },
        {
            'id': 7,
            'question': 'Как обозначается условие поставки «Франко перевозчик»?',
            'options': [
                {'id': 0, 'value': 'FCA', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'FAS'},
            ],
        },
        {
            'id': 8,
            'question': 'Как обозначается условие поставки «Свободно\nна борту»?',
            'options': [
                {'id': 0, 'value': 'FOB', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FCA'},
                {'id': 3, 'value': 'FAS'},
            ],
        },
        {
            'id': 9,
            'question': 'Как обозначается условие поставки «Свободно\nвдоль борта судна»?',
            'options': [
                {'id': 0, 'value': 'FAS', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FCA'},
                {'id': 3, 'value': 'FOB'},
            ],
        },
        {
            'id': 10,
            'question': 'Как обозначается условие поставки «Стоимость\nи фрахт»?',
            'options': [
                {'id': 0, 'value': 'CFR', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 11,
            'question': 'Как обозначается условие поставки «Перевозка\nи страхование оплачены до…»?',
            'options': [
                {'id': 0, 'value': 'CIP', 'is_correct': True},
                {'id': 1, 'value': 'CPT'},
                {'id': 2, 'value': 'CIF'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 12,
            'question': 'Как обозначается условие поставки «Перевозка оплачена до…»?',
            'options': [
                {'id': 0, 'value': 'CPT', 'is_correct': True},
                {'id': 1, 'value': 'CIP'},
                {'id': 2, 'value': 'CIF'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 13,
            'question': 'Как обозначается условие поставки «Стоимость, страхование и фрахт»?',
            'options': [
                {'id': 0, 'value': 'CIF', 'is_correct': True},
                {'id': 1, 'value': 'CIP'},
                {'id': 2, 'value': 'CPT'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 14,
            'question': 'Как обозначается условие поставки «Поставка\nс уплатой пошлины»?',
            'options': [
                {'id': 0, 'value': 'DDP', 'is_correct': True},
                {'id': 1, 'value': 'CIF'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DPU'},
            ],
        },
        {
            'id': 15,
            'question': 'Как обозначается условие поставки «Поставка\nв пункте назначения»?',
            'options': [
                {'id': 0, 'value': 'DAP', 'is_correct': True},
                {'id': 1, 'value': 'CIF'},
                {'id': 2, 'value': 'DDP'},
                {'id': 3, 'value': 'DPU'},
            ],
        },
        {
            'id': 16,
            'question': 'Как обозначается условие поставки «Поставка\nв место выгрузки»?',
            'options': [
                {'id': 0, 'value': 'DPU', 'is_correct': True},
                {'id': 1, 'value': 'CIF'},
                {'id': 2, 'value': 'DDP'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 17,
            'question': 'Какое обязательство группа «E» Инкотермс накладывает\nна продавца?',
            'options': [
                {'id': 0, 'value': 'Отгрузка', 'is_correct': True},
                {'id': 1, 'value': 'Основная перевозка не оплачена'},
                {'id': 2, 'value': 'Основная перевозка оплачена'},
                {'id': 3, 'value': 'Прибытие'},
            ],
        },
        {
            'id': 18,
            'question': 'Какое обязательство группа «F» Инкотермс накладывает\nна продавца?',
            'options': [
                {'id': 0, 'value': 'Основная перевозка не оплачена', 'is_correct': True},
                {'id': 1, 'value': 'Отгрузка'},
                {'id': 2, 'value': 'Основная перевозка оплачена'},
                {'id': 3, 'value': 'Прибытие'},
            ],
        },
        {
            'id': 19,
            'question': 'Какое обязательство группа «С» Инкотермс накладывает\nна продавца?',
            'options': [
                {'id': 0, 'value': 'Основная перевозка оплачена', 'is_correct': True},
                {'id': 1, 'value': 'Основная перевозка не оплачена'},
                {'id': 2, 'value': 'Отгрузка'},
                {'id': 3, 'value': 'Прибытие '},
            ],
        },
        {
            'id': 20,
            'question': 'Какое обязательство группа «D» Инкотермс накладывает\nна продавца? ',
            'options': [
                {'id': 0, 'value': 'Прибытие', 'is_correct': True},
                {'id': 1, 'value': 'Основная перевозка не оплачена'},
                {'id': 2, 'value': 'Отгрузка'},
                {'id': 3, 'value': 'Основная перевозка оплачена'},
            ],
        },
        {
            'id': 21,
            'question': 'Термины, применимые\nдля любого вида транспорта ',
            'options': [
                {'id': 0, 'value': 'EXW, FCA, CIP, CPT, DDP, DAP, DPU', 'is_correct': True},
                {'id': 1, 'value': 'EXW, FCA, FOB, CPT, DDP, DAP, DPU'},
                {'id': 2, 'value': 'FOB, FAS, CFR, CIF, DDP, DAP'},
                {'id': 3, 'value': 'EXW, FCA, FOB, CPT, DDP, DPU'},
            ],
        },
        {
            'id': 22,
            'question': 'Термины, применимые только для морского\nи внутреннего водного транспорта ',
            'options': [
                {'id': 0, 'value': 'FOB, FAS, CFR, CIF', 'is_correct': True},
                {'id': 1, 'value': 'EXW, FCA, CIP, CPT'},
                {'id': 2, 'value': 'EXW, FCA, FOB, CPT'},
                {'id': 3, 'value': 'EXW, FCA, FOB, CFR'},
            ],
        },
        {
            'id': 23,
            'question': 'Какие термины обязывают застраховать товар\nот всех рисков? ',
            'options': [
                {'id': 0, 'value': 'CIF, CIP', 'is_correct': True},
                {'id': 1, 'value': 'FCA, FOB '},
                {'id': 2, 'value': 'CIF, FCA '},
                {'id': 3, 'value': 'CIP, FOB '},
            ],
        },
        {
            'id': 24,
            'question': 'Какой термин накладывает минимальную ответственность\nна продавца?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 25,
            'question': 'Какой термин накладывает максимальную ответственность\nна продавца?',
            'options': [
                {'id': 0, 'value': 'DDP', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 26,
            'question': 'При каком условии поставки продавец обязан предоставить готовый\nк отгрузке товар?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 27,
            'question': 'При каком условии поставки покупатель обязан выполнить экспортное и импортное таможенное оформление, а также доставить товар?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 28,
            'question': 'При каком условии поставки риски переходят в момент передачи товара\nна складе продавца?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 29,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление\nи отгрузить товар перевозчику, назначенному покупателем?',
            'options': [
                {'id': 0, 'value': 'FCA', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 30,
            'question': 'При каком условии поставки покупатель обязан доставить товар\nи выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'FCA', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'DDP'},
                {'id': 3, 'value': 'CIF'},
            ],
        },
        {
            'id': 31,
            'question': 'При каком условии поставки риски переходят в момент передачи перевозчику\nна складе продавца?',
            'options': [
                {'id': 0, 'value': 'FCA', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 32,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление\nи разместить товар\nв порту отгрузки\nвдоль борта судна, указанного покупателем?',
            'options': [
                {'id': 0, 'value': 'FAS', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 33,
            'question': 'При каком условии поставки покупатель обязан погрузить товар\nна суднои д оставить\nв порт разгрузки, а также выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'FAS', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 34,
            'question': 'При каком условии поставки риски переходят в порту в момент размещения товара\nвдоль борта судна?',
            'options': [
                {'id': 0, 'value': 'FAS', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 35,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, доставить товар в порт отгрузки и погрузить\nна борт судна, указанного покупателем?',
            'options': [
                {'id': 0, 'value': 'FOB', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 36,
            'question': 'При каком условии поставки покупатель обязан доставить размещенный на борту судна товар в порт разгрузки, а также выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'FOB', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 37,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, погрузить товар на борт судна и доставить в порт разгрузки?',
            'options': [
                {'id': 0, 'value': 'CFR', 'is_correct': True},
                {'id': 1, 'value': 'FOB'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 38,
            'question': 'При каком условии поставки покупатель обязан принять прибывший в порт разгрузки товар,\nа также выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'CFR', 'is_correct': True},
                {'id': 1, 'value': 'FAS'},
                {'id': 2, 'value': 'CPT'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 39,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, застраховать, погрузить товар на борт судна\nи доставить в порт разгрузки?',
            'options': [
                {'id': 0, 'value': 'CIF', 'is_correct': True},
                {'id': 1, 'value': 'CFR'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 40,
            'question': 'При каком условии поставки покупатель обязан принять товар\nв порту разгрузки, разгрузить, а также выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'CIF', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'DDP'},
                {'id': 3, 'value': 'DAP'},
            ],
        },
        {
            'id': 41,
            'question': 'При каком условии поставки риски переходят в порту отгрузки\nс момента полной погрузки на борт судна?',
            'options': [
                {'id': 0, 'value': 'FOB', 'is_correct': True},
                {'id': 1, 'value': 'CFR'},
                {'id': 2, 'value': 'CIF'},
                {'id': 3, 'value': 'FAS'},
            ],
        },
        {
            'id': 42,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, застраховать и доставить груз в согласованное место назначения?',
            'options': [
                {'id': 0, 'value': 'CIP', 'is_correct': True},
                {'id': 1, 'value': 'CFR'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'FCA'},
            ],
        },
        {
            'id': 43,
            'question': 'При каком условии поставки риски переходят в момент передачи перевозчику на складе продавца? Продавец оплачивает транспортировку до места нахождения покупателя, но не несёт транспортных рисков. При этом страхует груз от транспортных рисков покупателя.',
            'options': [
                {'id': 0, 'value': 'CIP', 'is_correct': True},
                {'id': 1, 'value': 'CFR'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 44,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление\nи доставить груз\nв согласованное место назначения?',
            'options': [
                {'id': 0, 'value': 'CPT', 'is_correct': True},
                {'id': 1, 'value': 'DDP'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'CIF'},
            ],
        },
        {
            'id': 45,
            'question': 'При каком условии поставки риски переходят в момент передачи перевозчику на складе продавца? Продавец оплачивает транспортировку до места нахождения покупателя, но не несёт транспортных рисков.',
            'options': [
                {'id': 0, 'value': 'CPT', 'is_correct': True},
                {'id': 1, 'value': 'DAP'},
                {'id': 2, 'value': 'FCA'},
                {'id': 3, 'value': 'CIF'},
            ],
        },
        {
            'id': 46,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление\nи доставить груз\nдо согласованного пункта назначения?',
            'options': [
                {'id': 0, 'value': 'DAP', 'is_correct': True},
                {'id': 1, 'value': 'EXW'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'DDP'},
            ],
        },
        {
            'id': 47,
            'question': 'При каком условии поставки риски переходят в пункте назначения?',
            'options': [
                {'id': 0, 'value': 'DAP', 'is_correct': True},
                {'id': 1, 'value': 'FCA'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'EXW'},
            ],
        },
        {
            'id': 48,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, доставить товар до места назначения и выгрузить его?',
            'options': [
                {'id': 0, 'value': 'DPU', 'is_correct': True},
                {'id': 1, 'value': 'CPT'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'CFR'},
            ],
        },
        {
            'id': 49,
            'question': 'При каких условиях поставки покупатель обязан выполнить импортное таможенное оформление?',
            'options': [
                {'id': 0, 'value': 'CIP, CPT, DAP, DPU', 'is_correct': True},
                {'id': 1, 'value': 'EXW, FCA, FAS, FOB'},
                {'id': 2, 'value': 'EXW, FAS, FOB'},
                {'id': 3, 'value': 'EXW, FCA'},
            ],
        },
        {
            'id': 50,
            'question': 'При каком условии поставки риски переходят от продавца к покупателю в месте назначения после полной выгрузки?',
            'options': [
                {'id': 0, 'value': 'DPU', 'is_correct': True},
                {'id': 1, 'value': 'DAP'},
                {'id': 2, 'value': 'FOB'},
                {'id': 3, 'value': 'CPT'},
            ],
        },
        {
            'id': 51,
            'question': 'При каком условии поставки продавец обязан выполнить экспортное таможенное оформление, доставить груз\nдо согласованного места назначения и выполнить импортное таможенное оформление с уплатой пошлин?',
            'options': [
                {'id': 0, 'value': 'DDP', 'is_correct': True},
                {'id': 1, 'value': 'CPT'},
                {'id': 2, 'value': 'CFR'},
                {'id': 3, 'value': 'FOB'},
            ],
        },
        {
            'id': 52,
            'question': 'При каком условии поставки все риски несет покупатель?',
            'options': [
                {'id': 0, 'value': 'EXW', 'is_correct': True},
                {'id': 1, 'value': 'DPU'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'FOB'},
            ],
        },
        {
            'id': 53,
            'question': 'При каком условии поставки все риски несет продавец?',
            'options': [
                {'id': 0, 'value': 'DDP', 'is_correct': True},
                {'id': 1, 'value': 'DPU'},
                {'id': 2, 'value': 'DAP'},
                {'id': 3, 'value': 'FOB'},
            ],
        },
    ],
}

variant1 = PR1ControlVariant(
    product_price=7500,
    product_quantity=2,
    loading_expenses=100,
    delivery_to_unloading_port=300,
    loading_on_board=200,
    transport_expenses_to_port=2000,
    products_insurance=1000,
    incoterms=[Incoterm.EXW, Incoterm.FAS, Incoterm.FOB],
    **raw_pr1_control_info
)

pr1_control_info = PR1ControlInfo(variants=[variant1], **raw_pr1_control_info)
