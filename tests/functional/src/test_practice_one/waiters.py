import asyncio

from ....student_client import StudentClient
from ....teacher_client import TeacherClient


def student_waiter(student_client_parameters: dict):
    asyncio.run(student_client.connect_and_listen())


def teacher_waiter(teacher_client: TeacherClient):
    asyncio.run(teacher_client.connect_and_listen())
