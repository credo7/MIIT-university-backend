import logging
import copy
from datetime import datetime
from typing import List

import pymongo
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from db.mongo import get_db, CollectionNames
import schemas
from services import oauth2, utils
from services.utils import normalize_mongo

router = APIRouter(tags=['Users'], prefix='/users')

logger = logging.getLogger(__name__)


@router.get('', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
async def get_users(
    search: str = Query(None, description='Search by first name, last name, or surname'),
    group_id: str = Query(None, description='Filter by group ID'),
    sort: str = Query(None, description='AZ or ZA'),
    _current_user: schemas.FullUser = Depends(oauth2.get_current_user),
):
    found_users = utils.search_users_by_group(schemas.UserSearch(search=search, group_id=group_id), sort)
    return normalize_mongo(found_users, schemas.UserOut)


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def edit(
    user_update: schemas.UserUpdate,
    current_user: schemas.FullUser = Depends(oauth2.get_current_user),
    db: Database = Depends(get_db),
):
    if user_update.first_name:
        user_update.first_name = user_update.first_name.capitalize()
    if user_update.last_name:
        user_update.last_name = user_update.last_name.capitalize()
    if user_update.surname:
        user_update.surname = user_update.surname.capitalize()
    if user_update.student_id:
        user_update.student_id = user_update.student_id.upper()

    try:
        group_filter = {}
        if user_update.group_id:
            group_filter['_id'] = ObjectId(user_update.group_id)

        user_update_dict = {}
        if group_filter:
            group_db = db[CollectionNames.GROUPS.value].find_one(group_filter)
            if not group_db:
                raise HTTPException(status.HTTP_404_NOT_FOUND, 'Группа не найдена')
            user_update.group_id = str(group_db['_id'])
            user_update_dict['group_name'] = group_db['name']

        required_fields = ['first_name', 'last_name', 'surname', 'student_id', 'group_id']
        required_to_change = current_user.fix_for_approve_fields
        for field, value in user_update.dict().items():
            if field in required_fields and value is not None:
                if required_to_change:
                    if field in required_to_change:
                        required_to_change.remove(field)

                user_update_dict[field] = value

        if required_to_change:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder(
                    {'detail': 'Заполнены не все требуемые поля!', 'rest_fields': required_to_change,}
                ),
            )

        candidate = db[CollectionNames.USERS.value].find_one(
            {
                '_id': {'$ne': ObjectId(current_user.id)},
                'first_name': user_update_dict.get('first_name') or current_user.first_name,
                'last_name': user_update_dict.get('last_name') or current_user.last_name,
                'surname': user_update_dict.get('surname') or current_user.surname,
                'group_id': user_update_dict.get('group_id') or current_user.group_id,
                'student_id': user_update_dict.get('student_id') or current_user.student_id,
            }
        )
        if candidate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail='DUPLICATE_USER_ERROR',
            )

        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(current_user.id)},
            {'$set': {**user_update_dict, 'fix_for_approve_fields': None, 'updated_at': datetime.now()}},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        logger.info(f'user_update={user_update}')
        logger.info(f'current_user={current_user}')
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/approve/all', status_code=status.HTTP_200_OK)
async def approve_all(
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    group_id: str = None,
    db: Database = Depends(get_db),
):
    filter = {'approved': False, 'fix_for_approve_fields': None}
    if group_id:
        filter['group_id'] = group_id
    db[CollectionNames.USERS.value].update_many(filter, {"$set": {'approved': True}})


@router.post('/approve/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def approve_user(
    user_id: str,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    try:
        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(user_id)},
            {'$set': {'approved': True, 'updated_at': datetime.now()}},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        if not user_db:
            raise HTTPException(status_code=404, detail='Кандидат на апрув не найден')

        logger.info(f'user approved {user_db}')

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/request-edits', status_code=status.HTTP_200_OK)
async def request_edits(
    body: schemas.RequestEditsBody,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    fix_for_approve_fields = [
        field_name for field_name, field_value in body.__dict__.items() if field_value and field_name != 'user_id'
    ]

    if len(fix_for_approve_fields) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Поля не заданы.')

    user_db = db[CollectionNames.USERS.value].find_one_and_update(
        {'_id': ObjectId(body.user_id), 'approved': False},
        {'$set': {'fix_for_approve_fields': fix_for_approve_fields, 'updated_at': datetime.now()}},
    )

    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Студент не найден либо уже подтвержден')


@router.get('/check-approval', response_model=schemas.CheckApprovalResponse)
async def check_approval(current_user: schemas.FullUser = Depends(oauth2.get_current_user),):
    if current_user.approved:
        return schemas.CheckApprovalResponse(is_approved=True)
    if current_user.fix_for_approve_fields:
        return schemas.CheckApprovalResponse(is_approved=False, fields_to_be_fixed=current_user.fix_for_approve_fields)
    return schemas.CheckApprovalResponse(is_approved=False)


@router.get('/unapproved', status_code=status.HTTP_200_OK, response_model=List[schemas.UserToApprove])
async def get_unapproved_users(
    group_id: str = None,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    try:
        filter = {'approved': False, 'fix_for_approve_fields': None}
        if group_id:
            filter['group_id'] = group_id
        unapproved_users_db = db[CollectionNames.USERS.value].find(filter)
        return normalize_mongo(unapproved_users_db, schemas.UserToApprove)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/change-password', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def change_password(body: schemas.ChangePasswordBody, db: Database = Depends(get_db)):
    user_db = db[CollectionNames.USERS.value].find_one(
        {'last_name': body.last_name.capitalize(), 'student_id': body.student_id.upper()}
    )

    hash_password = utils.hash(body.new_password)

    if user_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')

    user = normalize_mongo(user_db, schemas.UserOut)

    db[CollectionNames.USERS.value].update_one(
        {'_id': ObjectId(user.id)}, {'$set': {'password': hash_password, 'updated_at': datetime.now()}}
    )

    return user


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.GetUserResponse)
async def get_user(id: str, db: Database = Depends(get_db)):
    user_db = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(id)})

    if not user_db:
        raise HTTPException(status_code=404, detail='User not found')

    user = normalize_mongo(user_db, schemas.UserOut)

    return schemas.GetUserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        surname=user.surname,
        username=user.username,
        group_id=user.group_id,
        group_name=user.group_name,
        history=user.history,
    )


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
async def delete_user(
    user_id: str,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    deleted = db[CollectionNames.USERS.value].delete_one({'_id': ObjectId(user_id)})

    if deleted.deleted_count < 1:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    logger.info(f'user with id {user_id} was deleted')

    return {'message': 'Deleted'}


@router.post('/make-me-teacher', status_code=status.HTTP_200_OK)
async def make_teacher(
    current_user: schemas.FullUser = Depends(oauth2.get_current_user), db: Database = Depends(get_db),
):
    db[CollectionNames.USERS.value].update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'approved': True, 'role': 'TEACHER', 'updated_at': datetime.now()}},
    )
