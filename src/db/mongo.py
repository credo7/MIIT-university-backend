from enum import Enum

from pymongo import MongoClient
from pymongo.database import Database

from core.config import settings


class CollectionNames(str, Enum):
    PRACTICE_ONE_INFO = "practice_one_info"
    LESSONS = "lessons"
    PR1_BETS = "practice_one.bets"
    EVENTS_SESSION = "events.session"
    EVENTS = "events"
    USERS = "users"
    GROUPS = "groups"
    LOGS = "logs"
    PR1_VARIANTS = "practice_one.variants"
    PR2_VARIANTS = "practice_two.variants"
    PR2_POINTS = "practice_two.points"
    PR2_CONTAINERS = "practice_two.containers"
    PR2_ROUTES = "practice_two.routes"
    PR2_RISKS = "practice_two.risks"
    CHECKPOINTS = "checkpoints"
    PR1_STEPS = "practice_one.steps"
    PR2_STEPS = "practice_two.steps"


mongo_client = MongoClient(settings.database_url)


def get_db() -> Database:
    return mongo_client['university']


def get_mongo_client() -> MongoClient:
    return mongo_client
