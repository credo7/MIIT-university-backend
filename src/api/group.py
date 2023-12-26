from functools import wraps
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from pymongo.database import Database

import schemas
from db.mongo import CollectionNames, get_db
from services import oauth2
from services.utils import normalize_mongo

router = APIRouter(tags=['Groups'], prefix='/groups')


# def auth_required(func):
#     @wraps(func)
#     async def wrapper(*args, **kwargs):
#         current_user: schemas.UserOut = kwargs.get("current_user")
#         await oauth2.is_teacher_or_error(user_id="current_user.id")
#         print(locals(), flush=True)
#         raise HTTPException(501, "MINE")
#         return await func(*args, **kwargs)
#
#     return wrapper


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
# @auth_required
async def create(
        group_create: schemas.GroupCreate,
        # current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db),
):
    # oauth2.is_teacher_or_error(user_id=current_user.id)

    candidate = db[CollectionNames.GROUPS.value].find_one({"name": group_create.name})

    if candidate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Группа с таким именем уже существует")

    inserted_group = db[CollectionNames.GROUPS.value].insert_one(group_create.dict())

    group_db = db[CollectionNames.GROUPS.value].find_one({"_id": inserted_group.inserted_id})
    group = await normalize_mongo(group_db, schemas.GroupOut)

    return group


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
async def get_groups(db: Database = Depends(get_db)):
    groups_db = db[CollectionNames.GROUPS.value].find()
    groups = await normalize_mongo(groups_db, schemas.GroupOut)
    return groups
