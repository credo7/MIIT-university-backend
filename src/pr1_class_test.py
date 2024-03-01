""" TODO:
1. Show results
2. WS Searching for user
3. Control work
4. Time spent
5. Show that users are connected
#  """

"""
0. _Connect by teacher in postman_

1. Student Starts_pr1_class
2. requests one by one with correct / not correct answers
3. checking results at the end
"""
from copy import deepcopy
import time

import websocket
import requests
from bson import ObjectId
from pymongo.database import Database
import threading

from constants.practice_one_info import practice_one_info
from db.mongo import get_db, CollectionNames
from schemas import PR1ClassEvent, EventType, EventMode
from services.utils import normalize_mongo


USER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjU4YWQzNDE2ZGNiN2M5N2VlNWNlMTFkIiwiZXhwIjoxNzA5MzE0MjMxfQ.yqNMAu-x6uU9SX4gRmnEL-Hcen0-yMlKADGPgii15IY'
USER_2_TOKEN = ""
COMPUTER_ID = 5
API_URL = 'http://localhost:3000'
WS_URL = f'ws://localhost:3000/ws/{COMPUTER_ID}'
EVENT_TYPE = EventType.PR1.value
EVENT_MODE = EventMode.CLASS.value

headers = {
    'Authorization': USER_TOKEN,
    # "Authorization2": USER_2_TOKEN,
}

start_request = {'computer_id': COMPUTER_ID, 'type': EVENT_TYPE, 'mode': EVENT_MODE}


def on_open(ws):
    print("Connection opened")
    ws.send("Hello, WebSocket!")


def on_message(ws, message):
    print(f"Received message: {message}")


def on_close(ws):
    print("Connection closed")



# ws = websocket.WebSocketApp(
#     WS_URL,
#     header=headers,
#     on_open=on_open,
#     on_message=on_message,
#     on_close=on_close
# )
#
# task = threading.Thread(target=ws.run_forever)
#
# task.start()
#
# time.sleep(3)

response = requests.post(f'{API_URL}/events/start', headers=headers, json=start_request)
print(f'response.status_code={response.status_code}')
event_id = response.json()['event_id']
print(event_id)

db: Database = get_db()

event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(event_id)})
event = normalize_mongo(event_db, PR1ClassEvent)


def get_right_checkpoints():
    checkpoints = []

    for step in practice_one_info.steps:
        checkpoint = {'step_code': step.code}
        if 'SELLER' in step.code or 'BUYER' in step.code:
            right_bets_ids = []
            for bet in practice_one_info.bets:
                incoterm = step.code[:3]
                if 'SELLER' in step.code:
                    if incoterm in bet.incoterms.seller:
                        right_bets_ids.append(bet.id)
                if 'BUYER' in step.code:
                    if incoterm in bet.incoterms.buyer or incoterm in bet.incoterms.common:
                        right_bets_ids.append(bet.id)
            checkpoint['answer_ids'] = right_bets_ids
        elif step.code == 'SELECT_LOGIST':
            checkpoint['chosen_index'] = 2
        elif step.code == "OPTIONS_COMPARISON":
            pass
        elif step.code == "CONDITIONS_SELECTION":
            checkpoint['chosen_incoterm'] = 'EXW'
        elif step.code == 'DESCRIBE_OPTION':
            checkpoint['text'] = 'Described.'
        else:
            test_index = int(step.code[5:]) - 1
            right_options_ids = [option.id for option in event.test[test_index].options if option.is_correct]
            checkpoint['answer_ids'] = right_options_ids
        checkpoints.append(checkpoint)

    return checkpoints

def make_exw_errors(checkpoints):
    temp = None
    temp_index = None
    for index, checkpoint in enumerate(checkpoints):
        if "EXW" in checkpoint["step_code"]:
            checkpoint["answer_ids"] = []
            temp = checkpoint
            temp_index = index
        break

    for i in range(2):
        checkpoints.insert(temp_index, temp)

def make_cip_two_tries(checkpoints):
    temp = None
    temp_index = None
    for index, checkpoint in enumerate(checkpoints):
        if "CIP" in checkpoint["step_code"]:
            temp = deepcopy(checkpoint)
            temp_index = index
            break

    temp["answer_ids"] = []

    for i in range(2):
        checkpoints.insert(temp_index, temp)

def make_test_error_7(checkpoints):
    temp = None
    temp_index = None
    for index, checkpoint in enumerate(checkpoints):
        if "TEST" in checkpoint["step_code"]:
            if "7" in checkpoint["step_code"]:
                temp = checkpoint
                temp["answer_ids"] = []
                temp_index = index
                break

    for i in range(2):
        checkpoints.insert(temp_index, temp)

def make_test_two_tries_13(checkpoints):
    temp = None
    temp_index = None
    for index, checkpoint in enumerate(checkpoints):
        if "TEST" in checkpoint["step_code"] and "13" in checkpoint["step_code"]:
            temp = deepcopy(checkpoint)
            temp_index = index
            break

    temp["answer_ids"] = []

    for i in range(2):
        checkpoints.insert(temp_index, temp)


if __name__ == "__main__":

    # Все ответы верны с первого раза, все common выбираются покупателем
    checkpoints = get_right_checkpoints()

    # make_exw_errors(checkpoints)
    # make_cip_two_tries(checkpoints)
    # make_test_error_7(checkpoints)
    # make_test_two_tries_13(checkpoints)

    params = {"event_id": event_id}

    for checkpoint in checkpoints:
        response = requests.get(
            f"{API_URL}/events/current-step/",
            params=params
        )

        print(f"\nCurrent-step={response.json()}")

        response = requests.post(
            f'{API_URL}/events/checkpoint',
            headers=headers,
            json={'computer_id': COMPUTER_ID, 'event_id': event_id, **checkpoint},
        )

        print(f"checkpoint_response={response.json()}")

        if response.status_code > 400:
            raise Exception("STOP")

    response = requests.get(f"{API_URL}/events/results", params={"event_id": event_id})
    print(response.json())

    time.sleep(5)
