import logging
from datetime import datetime
from typing import (
    List,
    Optional,
)

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pymongo.database import Database

import schemas
from db.mongo import (
    CollectionNames,
    get_db,
)
from services import oauth2
from services.utils import normalize_mongo

router = APIRouter(tags=['Groups'], prefix='/groups')

logger = logging.getLogger(__name__)


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
async def create(
    group_create: schemas.GroupCreate,
    # _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    candidate = db[CollectionNames.GROUPS.value].find_one({'name': group_create.name})

    if candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='GROUP_ALREADY_CREATED',
        )

    inserted_group = db[CollectionNames.GROUPS.value].insert_one(group_create.dict())

    group_db = db[CollectionNames.GROUPS.value].find_one({'_id': inserted_group.inserted_id})
    group = normalize_mongo(group_db, schemas.GroupOut)

    logger.info(f'group_created {group}')

    return group


@router.post('/hide/{group_id}', status_code=status.HTTP_200_OK)
async def hide_group(group_id: str, db: Database = Depends(get_db)):
    group_db = db[CollectionNames.GROUPS.value].find_one_and_update(
        {'_id': ObjectId(group_id)}, {'$set': {'is_hidden': True, "updated_at": datetime.now()}},
    )

    if not group_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Группа не найдена')


@router.post('/make-visible/{group_id}', status_code=status.HTTP_200_OK)
async def unhide_group(group_id: str, db: Database = Depends(get_db)):
    group_db = db[CollectionNames.GROUPS.value].find_one_and_update(
        {'_id': ObjectId(group_id)}, {'$set': {'is_hidden': False, "updated_at": datetime.now()}}
    )

    if not group_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Группа не найдена')


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
async def get_groups(show_hidden: Optional[bool] = False, db: Database = Depends(get_db)):
    filters = {}
    if not show_hidden:
        filters['$or'] = [{'is_hidden': False}, {'is_hidden': {'$exists': False}}]
    groups_db = db[CollectionNames.GROUPS.value].find(filters)
    groups = normalize_mongo(groups_db, schemas.GroupOut)
    return groups
