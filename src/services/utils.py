import copy
import random
import string
import json
from bson import json_util, ObjectId
from typing import Optional, List, Any, Union, Dict

from fastapi import HTTPException, status
from passlib.context import CryptContext
from transliterate import translit

from db.mongo import CollectionNames, Database, get_db
from schemas import UserSearch

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

db: Database = get_db()


def search_users_by_group(
    user_search: UserSearch
):
    filter = {}
    if user_search.search:
        names = user_search.search.split()

        if len(names) == 1:
            # Search by either first name or last name
            filter = {
                "$or": [
                    {"first_name": {"$regex": names[0]}},
                    {"last_name": {"$regex": names[0]}},
                    {"surname": {"$regex": names[0]}},
                ]
            }

        elif len(names) == 2:
            # Search by both first name and last name
            filter = {
                "$or": [
                    {
                        "$and": [
                            {"first_name": {"$regex": names[0]}},
                            {"last_name": {"$regex": names[1]}},
                        ]
                    },
                    {
                        "$and": [
                            {"first_name": {"$regex": names[1]}},
                            {"last_name": {"$regex": names[0]}},
                        ]
                    },
                ]
            }

        elif len(names) == 3:
            # Search by name, last name and surname
            filter = {
                "$or": [
                    {
                        "$and": [
                            {"first_name": {"$regex": names[0]}},
                            {"last_name": {"$regex": names[1]}},
                            {"surname": {"$regex": names[2]}},
                        ]
                    },
                    {
                        "$and": [
                            {"last_name": {"$regex": names[0]}},
                            {"first_name": {"$regex": names[1]}},
                            {"surname": {"$regex": names[2]}},
                        ]
                    },
                ]
            }

    if user_search.group_id is not None:
        filter["group_id"] = ObjectId(user_search.group_id)

    if user_search.group_name is not None:
        filter["group_name"] = user_search.group_name

    return db[CollectionNames.USERS.value].find(filter)



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
        if "_id" in temp_dict:
            temp_dict["id"] = temp_dict.pop("_id")
        if isinstance(exclude, List):
            for key in exclude:
                if key in exclude:
                    del temp_dict[key]
        return temp_dict

    if isinstance(obj, List):
        return [helper(dic) for dic in obj]
    else:
        return helper(obj)


async def normalize_mongo(db_obj, pydantic_schema, return_dict: bool = False) -> Any:
    if isinstance(db_obj, list):
        pydantic_objects = [pydantic_schema(**obj, id=str(obj["_id"])) for obj in db_obj]
        if return_dict:
            return [py_obj.dict() for py_obj in pydantic_objects]
        else:
            return pydantic_objects
    if isinstance(db_obj, dict):
        pydantic_object = pydantic_schema(**db_obj, id=str(db_obj["_id"]))
        if return_dict:
            return pydantic_object.dict()
        else:
            return pydantic_object
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Некорректный обьект")


async def to_db(obj, collection_name: CollectionNames) -> Union[List[str], str]:
    if isinstance(obj, list):
        return [str(inserted.inserted_id) for inserted in db[collection_name].insert_many(obj).inserted_ids]
    else:
        inserted = db[collection_name].insert_one(obj)
        return str(inserted.inserted_id)
