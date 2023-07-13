from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, oauth2, database

router = APIRouter(tags=['Groups'], prefix='/groups')


@router.post('/create', status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def create(
    group: schemas.GroupCreate,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db),
):

    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

    new_group = models.Group(**group.dict())
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemas.GroupOut])
def get_groups(db: Session = Depends(database.get_db)):
    groups = db.query(models.Group).all()
    return groups
