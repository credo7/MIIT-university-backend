from datetime import datetime, timedelta
from bson import ObjectId

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo.database import Database

import schemas
from core.config import settings
from db.mongo import get_db, CollectionNames
from services.utils import change_mongo_instance, normalize_mongo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, settings.access_token_secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception, raise_on_error=True):
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


def get_current_user(
        token: str = Depends(oauth2_scheme), raise_on_error=True, db: Database = Depends(get_db)
) -> schemas.UserOut:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f'Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    token = verify_access_token(token, credentials_exception, raise_on_error=raise_on_error)

    # TODO: Check! Maybe token.user_id
    user = db[CollectionNames.USERS.value].find_one({"_id": ObjectId(token.id)})

    return normalize_mongo(user, schemas.UserOut)


def is_teacher_or_error(user_id: str, db: Database = Depends(get_db)):
    user = db[CollectionNames.USERS.value].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    if user["role"] != schemas.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail='Only teacher authorized to access this endpoint')
    return user


def get_current_user_socket(token: str, db: Database = get_db()):
    user = None
    try:
        if 'Bearer' in token:
            token = token.split('Bearer ')[1]
        token = verify_access_token(token=token, credentials_exception=None, raise_on_error=False)
        user = db[CollectionNames.USERS.value].find_one({"_id": ObjectId(token.id)})
        return {**user, "_id": str(user["_id"])}
    except:
        ...
    return user
