import logging
from datetime import datetime, timedelta
from typing import List

from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.datastructures import Headers

import schemas
from core.config import settings
from db.mongo import CollectionNames, get_db
from services.utils import normalize_mongo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

logger = logging.getLogger(__name__)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, settings.access_token_secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception, raise_on_error=True) -> schemas.TokenData:
    try:
        payload = jwt.decode(token, settings.access_token_secret_key, algorithms=[settings.algorithm])

        id: str = payload.get('user_id')

        if id is None:
            raise credentials_exception

        token_data = schemas.TokenData(id=id)

    except JWTError:
        if raise_on_error:
            raise credentials_exception

        token_data = None

    return token_data


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, settings.access_token_secret_key, algorithms=[settings.algorithm])
        return payload.get('user_id', None)
    except Exception:
        return None


def extract_users_ids(headers: Headers):
    authorization = headers.get('Authorization')
    authorization2 = headers.get('Authorization2')

    tokens = []

    if authorization:
        if 'bearer' in authorization.lower():
            if len(authorization.split(' ')) > 1:
                token = authorization.split(' ')[1]
                tokens.append(token)
        else:
            tokens.append(authorization)

    if authorization2:
        if 'bearer' in authorization2.lower():
            if len(authorization2.split(' ')) > 1:
                token = authorization2.split(' ')[1]
                tokens.append(token)
        else:
            tokens.append(authorization2)

    users_ids = []

    for token in tokens:
        user_id = get_user_from_token(token)
        if user_id:
            users_ids.append(user_id)

    return users_ids


def extract_users_ids_rest(request: Request):
    return extract_users_ids(request.headers)


async def get_current_user(
    token: str = Depends(oauth2_scheme), raise_on_error=True, db: AsyncIOMotorDatabase = Depends(get_db)
) -> schemas.UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    token = verify_access_token(token, credentials_exception, raise_on_error=raise_on_error)

    user = await db[CollectionNames.USERS.value].find_one({'_id': ObjectId(token.id)})

    return normalize_mongo(user, schemas.UserOut)


async def get_current_teacher(token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)) -> schemas.UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    token = verify_access_token(token, credentials_exception)

    user_db = await db[CollectionNames.USERS.value].find_one({'_id': ObjectId(token.id)})

    if not user_db:
        raise Exception(f'Пользователь с ID {token.id} не найден')

    if user_db['role'] != schemas.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail='Only teacher authorized to access this endpoint')

    user = normalize_mongo(user_db, schemas.UserOut)

    return user


async def get_current_user_socket(token: str, db: AsyncIOMotorDatabase = None):
    try:
        if db is None:
            db = get_db()
        if 'Bearer' in token:
            token = token.split('Bearer ')[1]
        token = verify_access_token(token=token, credentials_exception=None, raise_on_error=False)
        user = await db[CollectionNames.USERS.value].find_one({'_id': ObjectId(token.id)})
        return {**user, '_id': str(user['_id'])}
    except Exception:
        return None


async def extract_ws_info_raise_if_teacher(headers: Headers) -> List[schemas.UserOut]:
    """Извлечение users_ids из bearer токенов в заголовках WebSocket"""
    db = get_db()

    rq_token1 = headers.get('authorization', None)
    rq_token2 = headers.get('authorization2', None)

    if not rq_token1:
        raise Exception('Токен в header authorization не был найден')

    if 'bearer' in rq_token1.lower():
        rq_token1 = rq_token1.split(' ')[1]

    if rq_token2 and 'bearer' in rq_token2.lower():
        rq_token2 = rq_token2.split(' ')[1]

    token1 = verify_access_token(token=rq_token1, credentials_exception=None, raise_on_error=False)

    token2 = None
    if rq_token2 is not None:
        token2 = verify_access_token(token=rq_token2, credentials_exception=None, raise_on_error=False)

    users = []

    for token in (token1, token2):
        if token is None:
            continue

        user_db = await db[CollectionNames.USERS.value].find_one({'_id': ObjectId(token.id)})
        user: schemas.UserOut = normalize_mongo(user_db, schemas.UserOut)
        users.append(user)

    if not users:
        raise Exception('Проверьте токены, хотя бы первый должен быть актуален и корректен')

    if len(users) == 2 and users[0].id == users[1].id:
        raise Exception('Вы пытаетесь авторизоваться с одного и того же аккаунта дважды')

    for user in users:
        if user.role == 'TEACHER':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail='Вебсокет предназначен только для студентов'
            )

    return users
