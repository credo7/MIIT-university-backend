import pytest
import requests
import redis

from enum import Enum
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import settings
from . import models
from . import testdata


class Role(str, Enum):
    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'


@pytest.fixture
def db_engine():
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    connection.close()


@pytest.fixture
def create_first_group_if_not_exist(db_session):
    group_exists = db_session.query(models.Group).filter(models.Group.id == 1).first()

    if not group_exists:
        new_group = models.Group(id=1, name='first group')
        db_session.add(new_group)
        db_session.commit()
        yield
        db_session.delete(new_group)
        db_session.commit()
    else:
        yield


@pytest.fixture
def redis():
    r = redis.StrictRedis(host='redis', port=6379, db=0)
    yield r



@pytest.fixture
def student_token_func(db_session, create_first_group_if_not_exist):
    def _get_student_token(num: int):
        response = requests.post(
            f'{settings.api_url}/auth/register',
            json=testdata.register_first_student if num == 1 else testdata.register_second_student,
        )
        assert response.status_code == 201, f'Failed to register student: {response.text}'

        token_response = response.json()
        token = token_response['access_token']
        username = token_response['username']

        yield token

        curr_user = db_session.query(models.User).filter(models.User.username == username).first()
        db_session.delete(curr_user)
        db_session.commit()

    return _get_student_token


@pytest.fixture
def teacher_token(db_session, create_first_group_if_not_exist):
    response = requests.post(f'{settings.api_url}/auth/register', json=testdata.register_teacher)
    assert response.status_code == 201, f'Failed to register teacher: {response.text}'

    token_response = response.json()
    token = token_response['access_token']
    username = token_response['username']

    curr_user = db_session.query(models.User).filter(models.User.username == username).first()
    curr_user.role = 'TEACHER'
    db_session.commit()

    yield token

    db_session.delete(curr_user)
    db_session.commit()
