from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean, UniqueConstraint, CheckConstraint
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Numeric
import enum

from database import Base, engine


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"

class EventMode(str, enum.Enum):
    CLASS = "CLASS"
    CONTROL = "CONTROL"
    WORKOUT = "WORKOUT"

class Incoterms(str, enum.Enum):
    EXW = "EXW"
    FCA = "FCA"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"
    FAS = "FAS"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"

class BetRole(str, enum.Enum):
    SELLER = "SELLER"
    BUYER = "BUYER"
    ALL = "ALL"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow())
    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    student = relationship("Student", uselist=False, back_populates="user")
    logs = relationship("Log", back_populates="user")

    def serialize(self):
        return {
            'id': self.id,
            'group_name': self.student.group.name,
            'first_name': self.first_name,
            'surname': self.surname,
            'lastname': self.last_name,
        }


class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    group_id = Column(Integer, ForeignKey("group.id"))

    user = relationship("User", back_populates="student")
    group = relationship("Group", back_populates="students")


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    students = relationship("Student", back_populates="group")


class Log(Base):
    __tablename__ = "log"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String)
    computer_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    process_time = Column(Numeric(10, 5), nullable=True)

    user = relationship("User", back_populates="logs", uselist=False)

class BetIncoterm(Base):
    __tablename__ = "bet_incoterm"

    id = Column(Integer, primary_key=True)
    name = Column(Enum(Incoterms), nullable=False)
    role = Column(Enum(BetRole), nullable=False)
    bet_id = Column(Integer, ForeignKey("bet.id"), nullable=False)
    
    bet = relationship("Bet", back_populates="incoterms")

    def to_json(self):
        return {
            'name': self.name,
            'role': self.role
        }
    
    @staticmethod
    def to_json_list(incoterms):
        return [incoterm.to_json() for incoterm in incoterms]


class Bet(Base):
    __tablename__ = "bet"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rate = Column(Numeric, nullable=False)

    incoterms = relationship("BetIncoterm", back_populates="bet")

    def to_json(self):
        return {
            'name': self.name,
            'rate': str(self.rate),
            'incoterms': BetIncoterm.to_json_list(self.incoterms)
        }
    
    @staticmethod
    def to_json_list(bets):
        return [bet.to_json() for bet in bets]


class TestQuestion(Base):
    __tablename__ = "test_question"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("test.id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    wrong_option1 = Column(String, nullable=False)
    wrong_option2 = Column(String, nullable=False)
    wrong_option3 = Column(String, nullable=False)

    test = relationship("Test", back_populates="test_questions")

    def to_json(self):
        return {
            'question': self.question,
            'answer': self.answer,
            'wrong_option1': self.wrong_option1,
            'wrong_option2': self.wrong_option2,
            'wrong_option3': self.wrong_option3
        }
    
    @staticmethod
    def to_json_list(test_questions):
        return [question.to_json() for question in test_questions]


class Test(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True)

    test_questions = relationship("TestQuestion", back_populates="test")
    practice_one_variants = relationship("PracticeOneVariant", back_populates="test")

    def to_json(self):
        return {'questions': TestQuestion.to_json_list(self.test_questions)}


class PracticeOneVariant(Base):
    __tablename__ = "practice_one_variant"

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    right_logist = Column(String, nullable=False)
    wrong_logist1 = Column(String, nullable=False)
    wrong_logist2 = Column(String, nullable=False)
    test_id = Column(Integer, ForeignKey("test.id"), nullable=False)

    test = relationship("Test", back_populates="practice_one_variants")


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    
    events = relationship("Event", back_populates="session")


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    session_id = Column(ForeignKey(Session.id), nullable=False)
    type = Column(Integer, nullable=False)
    mode = Column(Enum(EventMode), nullable=False)
    practice_one_variant_id = Column(Integer, ForeignKey(PracticeOneVariant.id), nullable=False)
    computer_id = Column(Integer, nullable=False)
    user_1_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user_2_id = Column(Integer, ForeignKey(User.id), nullable=True)
    is_finished = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow())
   
    session = relationship("Session", back_populates="events")
    practice_one_variant = relationship("PracticeOneVariant")

    __table_args__ = (
        CheckConstraint('type >= 1 AND type <= 3', name='check_valid_values'),
    )

class PracticeOneStep(Base):
    __tablename__ = "practice_one_step"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)


class EventCheckpoint(Base):
    __tablename__ = "event_checkpoint"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey(Event.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    step_id = Column(Integer, ForeignKey(PracticeOneStep.id) , nullable=False)
    fails = Column(Integer, nullable=True)
    points = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())

    step = relationship("PracticeOneStep")

    __table_args__ = (
        UniqueConstraint('event_id', 'step_id', 'user_id'),
    )


Base.metadata.create_all(bind=engine)
