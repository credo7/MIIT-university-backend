from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pymongo.database import Database

import schemas
from db.mongo import get_db, CollectionNames
from services import oauth2, utils


router = APIRouter(tags=['Authentication'], prefix='/auth',)


@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=schemas.RegistrationToken)
def register(user_dto: schemas.UserCreateBody, db: Database = Depends(get_db)):
    if user_dto.role == 'TEACHER':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Only students can be created')

    group = db[CollectionNames.GROUPS.value].find_one({"name": user_dto.group_name})

    if not group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'Group with name {user_dto.group_name} is not found',
        )

    hashed_password = utils.hash(user_dto.password)

    username = utils.create_username(
        first_name=user_dto.first_name, last_name=user_dto.last_name, surname=user_dto.surname, group_name=group["name"],
    )
    candidate = db[CollectionNames.USERS.value].find_one({"username": username})

    if candidate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f'User with username {username} already exists',
        )
    new_user = {
        "username": username,
        "password": hashed_password,
        "first_name": user_dto.first_name,
        "last_name": user_dto.last_name,
        "surname": user_dto.surname,
        "group_name": group['name'],
        "group_id": str(group['_id']),
        "role": user_dto.role,
        "approved": False
    }
    new_user = db[CollectionNames.USERS.value].insert_one(new_user)
    access_token = oauth2.create_access_token(data={'user_id': str(new_user.inserted_id)})
    return {'username': username, 'access_token': access_token, 'token_type': 'bearer'}


@router.post('/login', response_model=schemas.Token)
def login(
    user_dto: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db),
):
    user = db[CollectionNames.USERS.value].find_one({"username": user_dto.username})

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(user_dto.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = oauth2.create_access_token(data={'user_id': str(user["_id"])})

    return {'access_token': access_token, 'token_type': 'bearer'}
