import pickle
import time
from multiprocessing import Process, Manager
from time import sleep
import copy

import redis
import asyncio
from asyncio import Queue

from ....teacher_client import TeacherClient
from ....student_client import StudentClient
from ....custom_socketio_client import CustomSocketIOClient
from ...config import settings
from .waiters import student_waiter, teacher_waiter


def run_client(student_client: StudentClient):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    r.rpush('logs', 'in_run_client')
    student_client.connect_and_listen()
    r.rpush('logs', 'after_student_client_connect')


def student_listener_with_message_consumer(student_client: StudentClient):
    student_listener = Process(target=run_client, args=(student_client,))
    student_listener.start()

    while True:
        r = redis.StrictRedis(host='localhost', port=6379, db=0)

        if message := r.lpop('send_logs'):
            student_client.send_logs(message)


def produce_logs():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    i = 0
    while True:
        sleep(5)
        r.rpush('send_logs', f"Message number is {i}")
        i += 1


def test_practice_one(student_token_func, teacher_token):
    first_student_token = next(student_token_func(1))

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    r.flushdb()
    r.rpush('logs', 'application_started')

    base_client_parameters = {
        "api_url":settings.api_url,
        "socket_url":settings.socket_url
    }

    student_client = StudentClient(
        **base_client_parameters,
        user_token=first_student_token,
        computer_id=3,
        client_name='First student',
        user_token2=None)

    # student_process = Process(target=student_client.connect)
    # student_process.start()
    # sleep(1)
    def foo(sio):
        sio.emit('logs', 228)
    student_client.connect()
    student_client.sio.sleep(5)
    student_client.sio.send()
    student_client.sio.start_background_task(target=foo, sio=student_client.sio)
    student_client.sio.sleep(5)
    student_client.disconnect()

    # teacher_client = TeacherClient(
    #     **base_client_parameters,
    #     user_token=teacher_token,
    #     computer_id=1,
    #     client_name='Teacher',
    # )
    #
    # student_process = Process(target=student_listener_with_message_consumer, args=(student_client,))
    # student_process.start()
    #
    # producer_process = Process(target=produce_logs)
    # producer_process.start()
    #
    # sleep(120)

    # print("FINISHED", flush=True)
