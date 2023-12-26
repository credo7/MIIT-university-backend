from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pymongo.database import Database

import schemas
from db.mongo import get_db, CollectionNames
from services import oauth2, utils
from services.utils import normalize_mongo

router = APIRouter(tags=['Authentication'], prefix='/auth',)


@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=schemas.RegistrationResponse)
async def register(user_dto: schemas.UserCreateBody, db: Database = Depends(get_db)):
    group = db[CollectionNames.GROUPS.value].find_one({
        "_id": ObjectId(user_dto.group_id)
    })

    if not group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'Group with id {user_dto.group_id} is not found',
        )

    hashed_password = utils.hash(user_dto.password)

    username = utils.create_username(
        first_name=user_dto.first_name, last_name=user_dto.last_name, surname=user_dto.surname, group_name=group.name,
    )

    candidate = db[CollectionNames.USERS.value].find_one({
        "username": username
    })

    if candidate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f'User with username {username} already exists',
        )

    new_user = schemas.UserCreateDB(
        username=username,
        password=hashed_password,
        first_name=user_dto.first_name,
        last_name=user_dto.last_name,
        surname=user_dto.surname,
        group_id=user_dto.group_id,
        group_name=group["name"]
    )

    inserted_user = db[CollectionNames.USERS.value].insert_one(new_user.dict())
    user_db = db[CollectionNames.USERS.value].find_one({'_id': str(inserted_user.inserted_id)})
    user = await normalize_mongo(user_db, schemas.UserOut)

    access_token = oauth2.create_access_token(data={'user_id': str(inserted_user.inserted_id)})

    return {'username': username, 'access_token': access_token, 'token_type': 'bearer', 'user_info': user}


@router.post('/login', response_model=schemas.LoginResponse)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db),
):
    user_db = db[CollectionNames.USERS.value].find_one({
        "username": user_credentials.username
    })

    if not user_db:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Username not found')

    if not utils.verify(user_credentials.password, user_db.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    user: schemas.UserOutWithEvents = await normalize_mongo(user_db, schemas.UserOutWithEvents)

    access_token = oauth2.create_access_token(data={'user_id': user.id})

    return {'access_token': access_token, 'token_type': 'bearer', 'user_info': user}
