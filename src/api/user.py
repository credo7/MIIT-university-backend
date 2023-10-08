from typing import List, Optional

import pymongo.collection
from bson import ObjectId

from fastapi import APIRouter, Depends, HTTPException, status, Query

import schemas
from db.mongo import get_db, Database, CollectionNames
from services import oauth2, utils

router = APIRouter(tags=['Users'], prefix='/users')


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def edit(
    user: schemas.UserEdit, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user['id'], db=db)
        user_from_db = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(user.id)})
        if not user_from_db:
            raise HTTPException(status_code=404, detail='User not found')

        user_data = {k: v for k, v in vars(user).items() if v is not None}

        user_out = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(user.id)}, {'$set': user_data}, return_document=pymongo.collection.ReturnDocument.AFTER
        )

        return schemas.UserOut.mongo_to_json(user_out)
    except HTTPException as e:
        raise e
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get('/', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
def get_users(
    search: str = Query(None, description='Search by first name, last name, or surname'),
    group_id: str = Query(None, description='Filter by group ID'),
    _current_user=Depends(oauth2.get_current_user),
    db: Database = Depends(get_db),
):
    try:
        found_users = utils.search_users_with_group_id(db=db, search=search, group_id=group_id)
        return [schemas.UserOut.mongo_to_json(user) for user in found_users]
    except HTTPException as e:
        raise e
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/approve/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
def approve_user(user_id: str, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db)):
    oauth2.is_teacher_or_error(user_id=current_user["id"], db=db)

    user_from_db = db[CollectionNames.USERS.value].find_one_and_update(
        {'_id': ObjectId(user_id), "approved": False}, {"$set": {'approved': True}},
        return_document=pymongo.collection.ReturnDocument.AFTER
    )

    if not user_from_db:
        raise HTTPException(status_code=404, detail='User not found or already approved')

    return {'message': 'ok!'}


@router.get('/unapproved', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
def get_unapproved_users(
    group_id: str = None, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db)
):
    oauth2.is_teacher_or_error(user_id=current_user["id"], db=db)
    try:
        filter = {'approved': False}
        if group_id:
            filter['group_id'] = ObjectId(group_id)

        unapproved_users = db[CollectionNames.USERS.value].find(filter)

        return [schemas.UserOut.mongo_to_json(user) for user in unapproved_users]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.patch(
    '/change-password/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserChangePassword,
)
def change_password(
    user_id: str, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db)
):
    oauth2.is_teacher_or_error(user_id=current_user["id"], db=db)
    try:
        new_password = utils.generate_password()
        hash_password = utils.hash(new_password)

        res = utils.verify(new_password, hash_password)

        print(f"\nutils.verify = {res}\n")
        print(f"hash = {hash_password}")

        user_from_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(user_id)}, {"$set": {'password': hash_password}},
            return_document=pymongo.collection.ReturnDocument.AFTER
        )

        if not user_from_db:
            raise HTTPException(status_code=404, detail='User not found')

        return {'password': new_password}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def get_user(id: str, db: Database = Depends(get_db)):
    try:
        user = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(id)})

        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        return schemas.UserOut.mongo_to_json(user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
def delete_user(
    user_id: str, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user["id"], db=db)
    try:
        response = db[CollectionNames.USERS.value].delete_one({'_id': ObjectId(user_id)})

        if response.deleted_count < 1:
            raise HTTPException(status_code=404, detail='User not found')

        return {'message': 'ok!'}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')
