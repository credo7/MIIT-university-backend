from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from pymongo.database import Database

import schemas
from db.mongo import CollectionNames, get_db
from services import oauth2
from services.utils import normalize_mongo

router = APIRouter(tags=['Groups'], prefix='/groups')


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
async def create(
        group_create: schemas.GroupCreate,
        current_user: schemas.UserOut = Depends(oauth2.get_current_user),
        db: Database = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user.id)

        candidate = db[CollectionNames.GROUPS.value].find_one({"name": group_create.name})

        if candidate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Группа с таким именем уже существует")

        inserted_group = db[CollectionNames.GROUPS.value].insert_one(group_create.dict())

        group_db = db[CollectionNames.GROUPS.value].find_one({"_id": inserted_group.inserted_id})
        group = await normalize_mongo(group_db, schemas.GroupOut)

        return group
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
async def get_groups(db: Database = Depends(get_db)):
    groups_db = db[CollectionNames.GROUPS.value].find()
    groups = await normalize_mongo(groups_db, schemas.GroupOut)
    return groups
