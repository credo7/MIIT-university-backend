from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Numeric
import enum

from database import Base, engine


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


# class EventType(str, enum.Enum):
#     PR1 = "PR1"
#     PR2 = "PR2"
#     PR3 = "PR3"
#
#
# class EventMode(str, enum.Enum):
#     CLASS = "CLASS"
#     WORK_OUT = "WORK_OUT"
#     CONTROL = "CONTROL"


class User(Base):
    __tablename__ = "users"

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
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    group_id = Column(Integer, ForeignKey("groups.id"))

    user = relationship("User", back_populates="student")
    group = relationship("Group", back_populates="students")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    students = relationship("Student", back_populates="group")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String)
    computer_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    process_time = Column(Numeric(10, 5), nullable=True)

    user = relationship("User", back_populates="logs", uselist=False)


# class Bet(Base):
#     __tablename__ = "bets"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     rate = Column(Numeric, nullable=False)
#
#
# class PracticeOneVariant(Base):
#     __tablename__ = "practice_one_variants"
#
#     id = Column(Integer, primary_key=True, index=True)
#     description = Column(String, nullable=False)
#
#
# class PracticeOneBet(Base):
#     __tablename__ = "practice_one_bets"
#
#     id = Column(Integer, primary_key=True)
#     bet_id = Column(Integer, ForeignKey(Bet.id), nullable=False)
#     variant_id = Column(Integer, ForeignKey(PracticeOneVariant.id), nullable=False)
#
#     bet = relationship(Bet)
    # practice_one_variants = relationship(PracticeOneVariant, back_populates="bets", uselist=True)


# class PracticeTwoVariant(Base):
#     __tablename__ = "practice_two_variants"
#
#     id = Column(Integer, primary_key=True, index=True)
#
#
# class Event(Base):
#     __tablename__ = "events"
#
#     id = Column(Integer, primary_key=True, index=True)
#     type = Column(Enum(EventType), nullable=False)
#     mode = Column(Enum(EventMode), nullable=False)
#     variant_id = Column(Integer, nullable=False)
#
#     variant = relationship(
#         lambda: PracticeOneVariant if Event.type == EventType.PR1 else PracticeTwoVariant,
#         foreign_keys=[variant_id]
#     )


# class TableQuiz(Base):
#     id = Column(Integer, primary_key=True)
#     event_id = Column(Integer, ForeignKey(Event.id), nullable=False)
#     bet_id = Column(Integer, ForeignKey(Bet.id), nullable=False)
#     attempt = Column(Integer, default=1)


# class IncoTerms(Base):
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)


# class EventPair:
#     __tablename__ = "event_pairs"
#
#     id = Column(Integer, primary_key=True, index=True)
#     event_id = Column(Integer, ForeignKey("event.id"), nullable=False)
#
#
# class EventPairUser:
#     __tablename__ = "event_pair_users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     pair_id = Column(Integer, ForeignKey("event_pairs.id"), nullable=False)


Base.metadata.create_all(bind=engine)
