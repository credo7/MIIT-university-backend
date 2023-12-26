import copy
from typing import List, Any
from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database

from db.mongo import get_db, CollectionNames
import schemas
from services import oauth2, utils
from services.utils import change_mongo_instance, normalize_mongo

router = APIRouter(tags=['Users'], prefix='/users')


@router.get('', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
async def get_users(
    search: str = Query(None, description='Search by first name, last name, or surname'),
    group_id: str = Query(None, description='Filter by group ID'),
    group_name: str = Query(None, description='Filter by group name'),
    _current_user: schemas.FullUser = Depends(oauth2.get_current_user),
):
    try:
        found_users = utils.search_users_by_group(
            schemas.UserSearch(search=search, group_id=group_id, group_name=group_name)
        )
        return normalize_mongo(found_users, schemas.UserOut)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def edit(
        user_update: schemas.UserUpdate,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

        user_db = db[CollectionNames.USERS.value].find_one({
            "_id": ObjectId(current_user.id)
        })

        if not user_db:
            raise HTTPException(status_code=404, detail='User not found')

        group_filter = {}
        if user_update.group_id:
            group_filter["_id"] = ObjectId(user_update.group_id)
        if user_update.group_name:
            group_filter["name"] = user_update.group_name

        if group_filter:
            group_db = db[CollectionNames.GROUPS.value].find_one(group_filter)
            if not group_db:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Группа не найдена")
            user_update.group_id = str(group_db['_id'])
            user_update.group_name = group_db["name"]

        user_db = db[CollectionNames.GROUPS.value].find_one_and_update(
            {"_id": ObjectId(current_user.id)},
            {
                "$set": user_update.dict()
            }
        )

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('approve/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
async def approve_user(
        user_id: str,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db)
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "approve": True
                }
            }
        )

        if not user_db:
            raise HTTPException(status_code=404, detail='Кандидат на апрув не найден')

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get('/unapproved', status_code=status.HTTP_200_OK, response_model=List[schemas.UserToApprove])
async def get_unapproved_users(
        group_id: str = None,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db)
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        filter = {"approved": False}
        if group_id:
            filter["group_id"] = group_id
        unapproved_users_db = db[CollectionNames.USERS.value].find(filter)
        return normalize_mongo(unapproved_users_db, schemas.UserOut, return_dict=True)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.patch(
    '/change-password/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserCredentials,
)
async def change_password(
        user_id: str,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        new_password = utils.generate_password()

        hash_password = utils.hash(new_password)

        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(user_id)},
            {
                "$set": {
                    "password": hash_password
                }
            }
        )

        if not user_db:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        return schemas.UserCredentials(username=user_db["username"], password=new_password).dict()
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get('/{username}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def get_user(username: str, db: Database = Depends(get_db)):
    try:
        user_db = db[CollectionNames.USERS.value].find_one({
            "username": username
        })

        if not user_db:
            raise HTTPException(status_code=404, detail='User not found')

        return normalize_mongo(user_db, schemas.UserOut, return_dict=True)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
async def delete_user(
        user_id: str,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        deleted = db[CollectionNames.USERS.value].delete_one({'_id': ObjectId(user_id)})

        if deleted.deleted_count < 1:
            raise HTTPException(status_code=404, detail='Пользователь не найден')

        return {'message': 'Deleted'}
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')
