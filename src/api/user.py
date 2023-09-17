from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

import schemas
from db.postgres import get_db
from models import User, Student
from services import oauth2, utils

router = APIRouter(tags=['Users'], prefix='/users')


@router.get('', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
def get_users(
    search: str = Query(None, description="Search by first name, last name, or surname"),
    group_id: int = Query(None, description="Filter by group ID"),
    _current_user: User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        found_users = utils.search_users_with_group_id(db=db, search=search, group_id=group_id)

        return [user.to_user_out() for user in found_users]
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def edit(
    user: schemas.UserEdit, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db),
):
    try:
        oauth2.is_teacher_or_error(user_id=current_user.id, db=db)

        user_from_db = db.query(User).filter(User.id == user.id).first()

        if not user_from_db:
            raise HTTPException(status_code=404, detail='User not found')

        user_data = {k: v for k, v in vars(user).items() if v is not None}

        db.query(User).filter(User.id == user.id).update(user_data)
        db.commit()
        db.refresh(user_from_db)

        user_out = schemas.UserOut.from_orm(user_from_db)
        user_out.group_id = user_from_db.student.group_id

        return user_out
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.post('approve/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
def approve_user(
        user_id: int, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db)
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        user_from_db = db.query(User).filter(User.id == user_id).first()

        if not user_from_db:
            raise HTTPException(status_code=404, detail='User not found')

        user_from_db.approved = True
        db.commit()

        return {'message': 'ok!'}
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.get('/unapproved', status_code=status.HTTP_200_OK, response_model=List[schemas.UserToApprove])
def get_unapproved_users(group_id: int = None, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        query = db.query(User).filter(User.approved == False)
        if group_id:
            query = query.join(User.student)
            query = query.filter(Student.group_id == group_id)

        unapproved_users = query.all()
        return [user.serialize() for user in unapproved_users]
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.patch(
    '/change-password/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserChangePassword,
)
def change_password(
    user_id: int, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        user_from_db = db.query(User).filter(User.id == user_id).first()

        if not user_from_db:
            raise HTTPException(status_code=404, detail='User not found')

        new_password = utils.generate_password()

        hash_password = utils.hash(new_password)

        user_from_db.password = hash_password
        db.commit()

        return {'password': new_password}
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.get('/{username}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
def get_user(username: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        user_out = schemas.UserOut.from_orm(user)
        user_out.group_id = user.student.group_id

        return user_out
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
def delete_user(
    user_id: int, current_user: User = Depends(oauth2.get_current_user), db: Session = Depends(get_db),
):
    oauth2.is_teacher_or_error(user_id=current_user.id, db=db)
    try:
        user_to_delete = db.query(User).filter(User.id == user_id).first()

        if not user_to_delete:
            raise HTTPException(status_code=404, detail='User not found')

        db.delete(user_to_delete)
        db.commit()

        return {"message": "ok!"}
    except Exception as e:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")
