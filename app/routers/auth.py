import database
import models
import oauth2
import schemas
import utils
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(tags=['Authentication'], prefix='/auth',)


@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=schemas.RegistrationToken)
def register(user: schemas.UserCreateBody, db: Session = Depends(database.get_db)):
    if user.role == 'TEACHER':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Only students can be created')

    group = db.query(models.Group).filter(models.Group.id == user.group_id).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'Group with id {user.group_id} is not found',
        )

    hashed_password = utils.hash(user.password)

    username = utils.create_username(
        first_name=user.first_name, last_name=user.last_name, surname=user.surname, group_name=group.name,
    )

    candidate = db.query(models.User).filter(models.User.username == username).first()

    if candidate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f'User with username {username} already exists',
        )

    new_user = models.User(
        username=username,
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        surname=user.surname,
        student=models.Student(group_id=user.group_id),
        role=user.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = oauth2.create_access_token(data={'user_id': new_user.id})

    return {'username': username, 'access_token': access_token, 'token_type': 'bearer'}


@router.post('/login', response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = oauth2.create_access_token(data={'user_id': user.id})

    return {'access_token': access_token, 'token_type': 'bearer'}
