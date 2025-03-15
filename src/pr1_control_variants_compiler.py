import random

from pymongo import MongoClient

from schemas import (
    Incoterm,
    PR1ControlEvent,
)
from services.utils import normalize_mongo

mongo_client = MongoClient('mongodb://root:example@79.174.93.53:27017/')

db = mongo_client['university']

event_db = db['events'].find({'event_type': 'PR1', 'event_mode': 'CONTROL', 'is_finished': True}).limit(5)[0]
event = normalize_mongo(event_db, PR1ControlEvent)

for index in range(5):
    doc = f'Контрольная работа ПР1\nВариант - {index+1}\n\n'

    doc += f'Исходные данные:\n'
    incoterms = list(Incoterm)
    random.shuffle(incoterms)
    incoterms = incoterms[:3]

    for incoterm in incoterms:
        right_answer = event.calculate(incoterm)
        legend = event.legend.format(incoterm)
        doc += f'incoterm: {incoterm}\nЛегенда:\n{legend}\nПравильный ответ: {right_answer}\n\n'

    with open(f'pr1_control_variant{index+1}.txt', 'w', encoding='utf-8') as file:
        file.write(str(doc))
