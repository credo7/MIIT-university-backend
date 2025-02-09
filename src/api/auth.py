from bson import ObjectId
import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pymongo.database import Database

import schemas
from db.mongo import get_db, CollectionNames
from db.state import WebsocketServiceState
from services import oauth2, utils
from services.utils import normalize_mongo

router = APIRouter(tags=['Authentication'], prefix='/auth')

logger = logging.getLogger(__name__)


@router.post(
    '/register', status_code=status.HTTP_201_CREATED, response_model=schemas.RegistrationResponse,
)
async def register(user_dto: schemas.UserCreateBody, db: Database = Depends(get_db)):
    group = db[CollectionNames.GROUPS.value].find_one({'_id': ObjectId(user_dto.group_id)})

    if not group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'Group with id {user_dto.group_id} is not found',
        )

    hashed_password = utils.hash(user_dto.password.lower())

    username = utils.create_username(
        first_name=user_dto.first_name,
        last_name=user_dto.last_name,
        surname=user_dto.surname,
        group_name=group['name'],
    ).lower()

    candidate = db[CollectionNames.USERS.value].find_one({
        'first_name': user_dto.first_name,
        'last_name': user_dto.last_name,
        'surname': user_dto.surname,
        'group_id':user_dto.group_id
    })

    if (
        candidate and
        candidate['first_name'] == user_dto.first_name
        and candidate['last_name'] == user_dto.last_name
        and candidate['surname'] == user_dto.surname
        and candidate['group_id'] == user_dto.group_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="USER_ALREADY_REGISTERED",
        )

    new_user = schemas.UserCreateDB(
        username=username,
        password=hashed_password,
        first_name=user_dto.first_name.capitalize(),
        last_name=user_dto.last_name.capitalize(),
        surname=user_dto.surname.capitalize() if user_dto.surname is not None else None,
        group_id=user_dto.group_id,
        group_name=group['name'],
        student_id=user_dto.student_id.upper(),
    )

    inserted_user = db[CollectionNames.USERS.value].insert_one(new_user.dict())
    user_db = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(inserted_user.inserted_id)})
    user = normalize_mongo(user_db, schemas.UserOut)

    access_token = oauth2.create_access_token(data={'user_id': str(inserted_user.inserted_id)})

    logger.info(f'User registered. user={user}')

    return {
        'username': username,
        'access_token': access_token,
        'token_type': 'bearer',
        'user_info': user,
    }


@router.post('/login', response_model=schemas.LoginResponse)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db),
):
    user_db = db[CollectionNames.USERS.value].find_one({'username': user_credentials.username.lower()})

    if not user_db:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Username not found')

    if not utils.verify(user_credentials.password.lower(), user_db['password']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    user: schemas.UserOutWithEvents = normalize_mongo(user_db, schemas.UserOutWithEvents)

    computer_id = WebsocketServiceState.is_user_connected(user.id)
    if computer_id != -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "ALREADY_CONNECTED",
                "message": f"Пользователь {user.username} уже авторизован за компьютером {computer_id}"
            },
        )

    access_token = oauth2.create_access_token(data={'user_id': user.id})

    logger.info(f'User logined. user={user}')

    return {'access_token': access_token, 'token_type': 'bearer', 'user_info': user}
