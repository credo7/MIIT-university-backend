import logging
import time
from datetime import datetime

from passlib.context import CryptContext
from pymongo import MongoClient
from pymongo.database import Database

from core.config import settings
from db.mongo import CollectionNames

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_database(retry_interval: int = 5, max_retries: int = 100) -> Database:
    retries = 0
    while True:
        try:
            database = MongoClient(settings.database_url)['university']
            database.command('ping')
            return database
        except Exception:
            logger.warning(f'Connection attempt {retries + 1}/{max_retries} failed. Retrying in {retry_interval} seconds')
            retries += 1
            time.sleep(retry_interval)


def init_collections(db: Database):
    """Create collections if they don't exist"""
    existing_collections = db.list_collection_names()

    for collection_name in CollectionNames:
        if collection_name.value not in existing_collections:
            db.create_collection(collection_name.value)
            logger.info(f'Created collection: {collection_name.value}')
        else:
            logger.info(f'Collection already exists: {collection_name.value}')


def init_default_group(db: Database) -> str:
    """Create default group if it doesn't exist, return group_id"""
    groups_collection = db[CollectionNames.GROUPS.value]

    default_group = groups_collection.find_one({'name': 'Default'})
    if default_group:
        logger.info('Default group already exists')
        return str(default_group['_id'])

    result = groups_collection.insert_one({
        'name': 'Default',
        'is_hidden': False,
        'updated_at': datetime.now()
    })
    logger.info(f'Created default group with id: {result.inserted_id}')
    return str(result.inserted_id)


def init_teacher_user(db: Database, group_id: str):
    """Create default teacher user if it doesn't exist"""
    users_collection = db[CollectionNames.USERS.value]

    existing_teacher = users_collection.find_one({'username': 'teacher'})
    if existing_teacher:
        logger.info('Teacher user already exists')
        return

    teacher_user = {
        'first_name': 'Teacher',
        'last_name': 'Admin',
        'surname': None,
        'student_id': 'TEACHER001',
        'username': 'teacher',
        'password': hash_password('1qasw23ed'),
        'role': 'TEACHER',
        'group_id': group_id,
        'group_name': 'Default',
        'approved': True,
        'history': [],
        'incoterms': {},
        'fix_for_approve_fields': None,
        'updated_at': datetime.now()
    }

    users_collection.insert_one(teacher_user)
    logger.info('Created teacher user (username: teacher, password: teacher123)')


if __name__ == '__main__':
    logger.info('Waiting for MongoDB connection...')
    db = get_database()
    logger.info('Connected to MongoDB')

    logger.info('Initializing collections...')
    init_collections(db)

    logger.info('Initializing default group...')
    group_id = init_default_group(db)

    logger.info('Initializing teacher user...')
    init_teacher_user(db, group_id)

    logger.info('Database initialization complete!')
