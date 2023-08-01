import random
import string

from passlib.context import CryptContext
from transliterate import translit

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_username(first_name, last_name, surname, group_name):
    first_name_en = translit(first_name, 'ru', reversed=True)[:2]
    last_name_en = translit(last_name, 'ru', reversed=True)[:2]
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
    if num * 10 % 1 != 0:
        return f'{num:.2f}'
    elif num % 1 != 0:
        return f'{num:.1f}'
    else:
        return f'{num:.0f}'
