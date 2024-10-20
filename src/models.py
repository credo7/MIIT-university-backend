import enum
import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Float, Numeric

import schemas
from db.postgres import Base, engine


class UserRole(str, enum.Enum):
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'


class WaitTimePointType(str, enum.Enum):
    START = 'START'
    STOP = 'STOP'


class EventMode(str, enum.Enum):
    CLASS = 'CLASS'
    CONTROL = 'CONTROL'
    WORKOUT = 'WORKOUT'


class RiskType(str, enum.Enum):
    TERMINAL = 'TERMINAL'
    PORT = 'PORT'
    ALL = 'ALL'


class Incoterms(str, enum.Enum):
    EXW = 'EXW'
    FCA = 'FCA'
    CPT = 'CPT'
    CIP = 'CIP'
    DAP = 'DAP'
    DPU = 'DPU'
    DDP = 'DDP'
    FAS = 'FAS'
    FOB = 'FOB'
    CFR = 'CFR'
    CIF = 'CIF'


class BetRole(str, enum.Enum):
    SELLER = 'SELLER'
    BUYER = 'BUYER'
    ALL = 'ALL'


class PointType(str, enum.Enum):
    TERMINAL = 'TERMINAL'
    PORT = 'PORT'
    COUNTRY = 'COUNTRY'


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    surname = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow())
    role = Column(String, default='STUDENT')
    # role = Column(Enum(UserRole), default=UserRole.STUDENT)
    approved = Column(Boolean, default=False)

    student = relationship('Student', uselist=False, back_populates='user')
    logs = relationship('Log', back_populates='user')

    def user_out(self):
        schemas.UserOut(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            surname=self.surname,
            approved=self.approved,
            group_name=self.student.group.name,
            group_id=self.student.group.id,
        )

    def serialize(self):
        return {
            'id': self.id,
            'group_name': self.student.group.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'surname': self.surname,
        }

    def to_user_out(self):
        return {
            'id': self.id,
            'group_name': self.student.group.name,
            'group_id': self.student.group.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'surname': self.surname,
            'approved': self.approved,
        }

    def to_json(self):
        return {
            'id': self.id,
            'group_name': self.student.group.name,
            'group_id': self.student.group.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'surname': self.surname,
            'approved': self.approved,
        }


class Risk(Base):
    __tablename__ = 'risk'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(RiskType), nullable=False)

    def to_json(self):
        return {'name': self.name, 'type': self.type}

    @staticmethod
    def to_json_list(risks):
        return [risk.to_json() for risk in risks]


class Student(Base):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)
    group_id = Column(Integer, ForeignKey('group.id'))

    user = relationship('User', back_populates='student')
    group = relationship('Group', back_populates='students')


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    students = relationship('Student', back_populates='group')


class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String)
    computer_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    process_time = Column(Numeric(10, 5), nullable=True)

    user = relationship('User', back_populates='logs', uselist=False)


class BetIncoterm(Base):
    __tablename__ = 'bet_incoterm'

    id = Column(Integer, primary_key=True)
    name = Column(Enum(Incoterms), nullable=False)
    role = Column(Enum(BetRole), nullable=False)
    bet_id = Column(Integer, ForeignKey('bet.id'), nullable=False)

    bet = relationship('Bet', back_populates='incoterms')

    def to_json(self):
        return {'name': self.name, 'role': self.role}

    @staticmethod
    def to_json_list(incoterms):
        return [incoterm.to_json() for incoterm in incoterms]


class Bet(Base):
    __tablename__ = 'bet'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rate = Column(Numeric, nullable=False)

    incoterms = relationship('BetIncoterm', back_populates='bet')

    def to_json(self):
        return {
            'name': self.name,
            'rate': str(self.rate),
            'incoterms': BetIncoterm.to_json_list(self.incoterms),
        }

    @staticmethod
    def to_json_list(bets):
        return [bet.to_json() for bet in bets]


class TestQuestion(Base):
    __tablename__ = 'test_question'

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    wrong_option1 = Column(String, nullable=False)
    wrong_option2 = Column(String, nullable=False)
    wrong_option3 = Column(String, nullable=False)

    test = relationship('Test', back_populates='test_questions')

    def to_json(self):
        return {
            'question': self.question,
            'answer': self.answer,
            'wrong_option1': self.wrong_option1,
            'wrong_option2': self.wrong_option2,
            'wrong_option3': self.wrong_option3,
        }

    @staticmethod
    def to_json_list(test_questions):
        return [question.to_json() for question in test_questions]


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)

    test_questions = relationship('TestQuestion', back_populates='test')
    practice_one_variants = relationship('PracticeOneVariant', back_populates='test')

    def to_json(self):
        return {'questions': TestQuestion.to_json_list(self.test_questions)}


class PracticeOneVariant(Base):
    __tablename__ = 'practice_one_variant'

    id = Column(Integer, primary_key=True)
    legend = Column(String, nullable=False)
    product_price = Column(Integer, nullable=False)
    right_logist = Column(String, nullable=False)
    wrong_logist1 = Column(String, nullable=False)
    wrong_logist2 = Column(String, nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)

    test = relationship('Test', back_populates='practice_one_variants')


class Point(Base):
    __tablename__ = 'point'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, Enum(PointType), nullable=False)
    country = Column(String, nullable=False)


class Route(Base):
    __tablename__ = 'route'

    id = Column(Integer, primary_key=True)
    from_point_id = Column(String, ForeignKey('point.id'), nullable=False)
    to_point_id = Column(String, ForeignKey('point.id'), nullable=False)
    days = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint('from_point_id', 'to_point_id'),)

    def __str__(self):
        return f'from_point_id: {self.from_point_id}\nto_point_id: {self.to_point_id}\ndays: {self.days}'


class PracticeTwoVariantBet(Base):
    __tablename__ = 'practice_two_variant_bet'

    id = Column(Integer, primary_key=True)
    variant_id = Column(Integer, ForeignKey('practice_two_variant.id'))
    from_point_id = Column(String, ForeignKey('point.id'), nullable=False)
    to_point_id = Column(String, ForeignKey('point.id'), nullable=False)
    transit_point_id = Column(String, ForeignKey('point.id'), nullable=False)
    tons = Column(Integer, nullable=False)
    third_party_logistics_1 = Column(Integer, nullable=True)
    third_party_logistics_2 = Column(Integer, nullable=True)
    third_party_logistics_3 = Column(Integer, nullable=True)
    answer = Column(String, nullable=False)

    from_point = relationship('Point', foreign_keys=[from_point_id])
    to_point = relationship('Point', foreign_keys=[to_point_id])
    transit_point = relationship('Point', foreign_keys=[transit_point_id])

    variant = relationship('PracticeTwoVariant')

    @property
    def answer_array(self):
        return json.loads(self.answer)

    def to_json(self):
        return {
            'from': self.from_point,
            'to': self.to_point,
            'through': self.transit_point,
            '3PL1': self.third_party_logistics_1,
            '3PL2': self.third_party_logistics_2,
            '3PL3': self.third_party_logistics_3,
            'tons': self.tons,
            'answer': json.loads(self.answer),
            'package_tons': self.variant.package_tons,
        }

    @staticmethod
    def to_json_list(rows):
        return [row.to_json() for row in rows]


class Container(Base):
    __tablename__ = 'container'

    id = Column(Integer, primary_key=True)
    size = Column(Integer, nullable=False)
    length = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    payload_capacity = Column(Float, nullable=False)

    def to_json(self):
        return {
            'size': self.size,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'payload_capacity': self.payload_capacity,
        }

    @staticmethod
    def to_json_list(containers):
        return [container.to_json() for container in containers]


class PracticeTwoVariant(Base):
    __tablename__ = 'practice_two_variant'

    id = Column(Integer, primary_key=True)
    legend = Column(String, nullable=False)
    package_length = Column(Float, nullable=False)
    package_width = Column(Float, nullable=False)
    package_height = Column(Float, nullable=False)
    package_tons = Column(Float, nullable=False)

    bets = relationship('PracticeTwoVariantBet', back_populates='variant')


class Lesson(Base):
    __tablename__ = 'lesson'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow())

    events = relationship('Event', back_populates='lesson')


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    lesson_id = Column(ForeignKey(Lesson.id), nullable=False)
    type = Column(Integer, nullable=False)
    mode = Column(Enum(EventMode), nullable=False)
    variant_one_id = Column(Integer, ForeignKey(PracticeOneVariant.id), nullable=True)
    variant_two_id = Column(Integer, ForeignKey(PracticeTwoVariant.id), nullable=True)
    computer_id = Column(Integer, nullable=False)
    user_1_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user_2_id = Column(Integer, ForeignKey(User.id), nullable=True)
    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow())

    lesson = relationship('Lesson', back_populates='events')
    practice_one_variant = relationship(PracticeOneVariant)
    practice_two_variant = relationship(PracticeTwoVariant)
    wait_time_points = relationship('EventWaitTimePoint', back_populates='events')

    __table_args__ = (CheckConstraint('type >= 1 AND type <= 3', name='check_valid_values'),)

    @property
    def variant(self):
        if self.type == 1:
            return self.practice_one_variant
        if self.type == 2:
            return self.practice_two_variant


class EventWaitTimePoint(Base):
    __tablename__ = 'wait_time_points'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey(Event.id), nullable=False)
    type = Column(Enum(WaitTimePointType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())

    events = relationship('Event', back_populates='wait_time_points')


class PracticeOneStep(Base):
    __tablename__ = 'practice_one_step'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(Enum(BetRole), nullable=False)


class PracticeTwoStep(Base):
    __tablename__ = 'practice_two_step'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class EventCheckpoint(Base):
    __tablename__ = 'event_checkpoint'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey(Event.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    pr1_step_id = Column(Integer, ForeignKey(PracticeOneStep.id), nullable=True)
    pr2_step_id = Column(Integer, ForeignKey(PracticeTwoStep.id), nullable=True)
    fails = Column(Integer, nullable=True)
    points = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())

    pr1_step = relationship('PracticeOneStep')
    pr2_step = relationship('PracticeTwoStep')

    __table_args__ = (
        UniqueConstraint('event_id', 'pr1_step_id', 'user_id'),
        UniqueConstraint('event_id', 'pr2_step_id', 'user_id'),
    )


Base.metadata.create_all(bind=engine)
