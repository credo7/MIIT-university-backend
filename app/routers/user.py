from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import database, models, oauth2, schemas, utils

router = APIRouter(tags=['Users'], prefix='/users')


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def edit(
    user: schemas.UserEdit,
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

    user_from_db = db.query(models.User).filter(models.User.id == user.id).first()

    if not user_from_db:
        raise HTTPException(status_code=404, detail='User not found')

    user_data = {k: v for k, v in vars(user).items() if v is not None}

    db.query(models.User).filter(models.User.id == user.id).update(user_data)
    db.commit()
    db.refresh(user_from_db)

    user_out = schemas.UserOut.from_orm(user_from_db)
    user_out.group_id = user_from_db.student.group_id

    return user_out


@router.patch(
    '/change-password/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserChangePassword,
)
def change_password(
    user_id: int, current_user: models.User = Depends(oauth2.get_current_user), db: Session = Depends(database.get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

    user_from_db = db.query(models.User).filter(models.User.id == user_id).first()

    if not user_from_db:
        raise HTTPException(status_code=404, detail='User not found')

    new_password = utils.generate_password()

    hash_password = utils.hash(new_password)

    print(user_from_db.password)
    user_from_db.password = hash_password
    db.commit()

    return {'password': new_password}


@router.get('/{username}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def get_user(username: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    user_out = schemas.UserOut.from_orm(user)
    user_out.group_id = user.student.group_id

    return user_out
