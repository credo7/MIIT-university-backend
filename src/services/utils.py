import random
import string
import json
from bson import json_util, ObjectId

from typing import Optional

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from transliterate import translit
from db.mongo import get_db, Database

from db.mongo import CollectionNames

# from models import User, Student

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def search_users_with_group_id(
    db: Database, search: Optional[str], group_id: Optional[str]
):
    filter = {}
    if search:
        names = search.split()

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

    if group_id is not None:
        try:
            filter["group_id"] = ObjectId(group_id)
        except Exception as e:
            raise Exception(f"Problem with group_id. {str(e)}")

    print(f"\nfilter is {filter}\n")

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
