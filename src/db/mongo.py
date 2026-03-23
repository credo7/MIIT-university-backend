from enum import Enum

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings


class CollectionNames(str, Enum):
    PRACTICE_ONE_INFO = 'practice_one_info'
    PR1_BETS = 'practice_one.bets'
    EVENTS_SESSION = 'events.session'
    EVENTS = 'events'
    USERS = 'users'
    GROUPS = 'groups'
    LOGS = 'logs'
    PR1_VARIANTS = 'practice_one.variants'
    PR2_VARIANTS = 'practice_two.variants'
    PR2_POINTS = 'practice_two.points'
    PR2_CONTAINERS = 'practice_two.containers'
    PR2_ROUTES = 'practice_two.routes'
    PR2_RISKS = 'practice_two.risks'
    CHECKPOINTS = 'checkpoints'
    PR1_STEPS = 'practice_one.steps'
    PR2_STEPS = 'practice_two.steps'


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    """Подключение к MongoDB с настройками пула соединений"""
    db.client = AsyncIOMotorClient(
        settings.database_url,
        maxPoolSize=10,
        minPoolSize=1,
        serverSelectionTimeoutMS=5000
    )


async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    if db.client:
        db.client.close()


def get_db() -> AsyncIOMotorDatabase:
    """Получение экземпляра базы данных"""
    return db.client['university']
