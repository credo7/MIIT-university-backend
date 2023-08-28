from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

import schemas
from db.postgres import get_db
from models import Group, User
from services import oauth2

router = APIRouter(tags=['Groups'], prefix='/groups')


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def create(
    group: schemas.GroupCreate, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

        new_group = Group(**group.dict())
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        return new_group
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
def get_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return groups
