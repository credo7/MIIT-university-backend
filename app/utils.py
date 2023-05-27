from passlib.context import CryptContext
from transliterate import translit
import random
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_username(first_name, last_name, surname, group_name):
    first_name_en = translit(first_name, 'ru', reversed=True)[:2]
    last_name_en = translit(last_name, 'ru', reversed=True)[:2]
    surname_en = translit(surname, 'ru', reversed=True)[:2]
    group_name_en = translit(group_name, 'ru', reversed=True)
    username_without_spaces = str.lower(first_name_en + last_name_en + surname_en + group_name_en).replace(" ", "")

    return username_without_spaces


def generate_password(length=8):
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for _ in range(length))
    return password


if __name__ == "__main__":
    print(create_username(first_name="Антон", last_name="Водкин", surname="Игоревич", group_name="УЭЦ-241 189"))
