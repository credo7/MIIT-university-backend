import copy
import random
import string
from bson import ObjectId
from typing import Optional, List, Any, Union, Dict, TypeVar

from passlib.context import CryptContext
from pydantic.main import BaseModel
from transliterate import translit
from pymongo.cursor import Cursor
import pymongo

from db.mongo import CollectionNames, Database, get_db
from schemas import UserSearch, ConnectedComputer

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

db: Database = get_db()


def search_users_by_group(user_search: UserSearch, sort: Optional[str] = None):
    filter = {'role': 'STUDENT'}
    if user_search.search:
        names = user_search.search.split()

        if len(names) == 1:
            # Search by either first name or last name
            filter = {
                '$or': [
                    {'first_name': {'$regex': names[0]}},
                    {'last_name': {'$regex': names[0]}},
                    {'surname': {'$regex': names[0]}},
                ]
            }

        elif len(names) == 2:
            # Search by both first name and last name
            filter = {
                '$or': [
                    {'$and': [{'first_name': {'$regex': names[0]}}, {'last_name': {'$regex': names[1]}},]},
                    {'$and': [{'first_name': {'$regex': names[1]}}, {'last_name': {'$regex': names[0]}},]},
                ]
            }

        elif len(names) == 3:
            # Search by name, last name and surname
            filter = {
                '$or': [
                    {
                        '$and': [
                            {'first_name': {'$regex': names[0]}},
                            {'last_name': {'$regex': names[1]}},
                            {'surname': {'$regex': names[2]}},
                        ]
                    },
                    {
                        '$and': [
                            {'last_name': {'$regex': names[0]}},
                            {'first_name': {'$regex': names[1]}},
                            {'surname': {'$regex': names[2]}},
                        ]
                    },
                ]
            }

    if user_search.group_id is not None:
        filter['group_id'] = user_search.group_id

    if user_search.group_name is not None:
        filter['group_name'] = user_search.group_name

    if sort is None or sort == 'AZ':
        return db[CollectionNames.USERS.value].find(filter).sort('last_name', pymongo.ASCENDING)
    else:
        return db[CollectionNames.USERS.value].find(filter).sort('last_name', pymongo.DESCENDING)


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_username(first_name, last_name, surname, group_name):
    first_name_en = translit(first_name, 'ru', reversed=True)[:2]
    last_name_en = translit(last_name, 'ru', reversed=True)[:2]
    surname_en = ''
    if surname:
        surname_en = translit(surname, 'ru', reversed=True)[:2]
    group_name_en = translit(group_name, 'ru', reversed=True)
    username_without_spaces = str.lower(first_name_en + last_name_en + surname_en + group_name_en).replace(' ', "")

    return username_without_spaces


def generate_password(length=8):
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for _ in range(length))
    return password


def formatting_number(num):
    """Formats a number without trailing zeros at the end.
        
        Examples:

        >>> f(3)
        '3'

        >>> f(3.456412)
        '3.45'

        >>> f(3.1)
        '3.1'
        """

    rounded_num = round(num, 2)
    if rounded_num.is_integer() or rounded_num * 100 % 100 == 0:
        return f'{rounded_num:.0f}'
    elif rounded_num * 100 % 10 == 0:
        return f'{rounded_num:.1f}'
    else:
        return f'{rounded_num:.2f}'


def change_mongo_instance(obj: Union[List, Dict], exclude: Optional[List[str]] = None):
    def helper(dictionary: dict):
        temp_dict = copy.copy(dictionary)
        if '_id' in temp_dict:
            temp_dict['id'] = temp_dict.pop('_id')
        if isinstance(exclude, List):
            for key in exclude:
                if key in exclude:
                    del temp_dict[key]
        return temp_dict

    if isinstance(obj, List):
        return [helper(dic) for dic in obj]
    else:
        return helper(obj)


T = TypeVar('T')


def normalize_mongo(db_obj, pydantic_schema: T, return_dict: bool = False) -> Union[T, list[T]]:
    if isinstance(db_obj, Cursor):
        db_obj = list(db_obj)
    if isinstance(db_obj, list):
        for obj in db_obj:
            obj['id'] = str(obj['_id'])
        pydantic_objects = [pydantic_schema(**obj) for obj in db_obj]
        if return_dict:
            return [py_obj.dict() for py_obj in pydantic_objects]
        else:
            return pydantic_objects
    if isinstance(db_obj, dict):
        db_obj['id'] = str(db_obj['_id'])
        pydantic_object = pydantic_schema(**db_obj)
        if return_dict:
            return pydantic_object.dict()
        else:
            return pydantic_object
    raise Exception(f'Некорректный обьект в normilize_mongo. db_obj={db_obj}')


def to_db(obj, collection_name: CollectionNames) -> Union[List[str], str]:
    if isinstance(obj, list):
        if isinstance(obj[0], BaseModel):
            obj = [instance.dict() for instance in obj]
        response = db[collection_name].insert_many(obj)
        return [str(id) for id in response.inserted_ids]
    else:
        if isinstance(obj, BaseModel):
            obj = obj.dict()
        inserted = db[collection_name].insert_one(obj)
        return str(inserted.inserted_id)


def raise_if_users_already_connected(
    connected_computers: Dict[int, ConnectedComputer], users_ids: List[str], ignore_computer_id: Optional[int] = None
):
    all_connected_users_ids = []
    for computer_id, computer in connected_computers.items():
        if ignore_computer_id is not None and computer_id == ignore_computer_id:
            continue

        all_connected_users_ids.extend(computer.users_ids)

    for user_id in users_ids:
        if user_id in all_connected_users_ids:
            raise Exception('User is already connected to another computer')


def normilize_id(db_obj):
    if isinstance(db_obj, list):
        for db_el in db_obj:
            db_el['id'] = str(db_el['_id'])
            del db_el['_id']
    else:
        db_obj['id'] = str(db_obj['_id'])
        del db_obj['_id']
    return db_obj


def format_with_spaces(num):
    return '{:,}'.format(num).replace(',', ' ')
