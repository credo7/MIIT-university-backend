from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from pymongo.database import Database

import schemas
from db.mongo import get_db, CollectionNames
from services import oauth2, utils

router = APIRouter(tags=['Groups'], prefix='/groups')


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def create(
    group: schemas.GroupCreate, current_user=Depends(oauth2.get_current_user), db: Database = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user["id"], db=db)

        if db[CollectionNames.GROUPS.value].find({"name": group.name}):
            raise Exception("Group is already exist")
        new_group = db[CollectionNames.GROUPS.value].insert_one({**group.dict()})

        return {"id": str(new_group.inserted_id), "name": group.name}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
def get_groups(db: Database = Depends(get_db)):
    groups = db[CollectionNames.GROUPS.value].find()
    return [{"id": str(group["_id"]), "name": group["name"]} for group in groups]
