from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import schemas
from core.config import settings
from db.postgres import get_db
from db.postgres import session as session_db
from models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, settings.access_token_secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception, raise_on_error=True):
    try:
        payload = jwt.decode(token, settings.access_token_secret_key, algorithms=[settings.algorithm])

        id: str = payload.get('user_id')

        if id is None:
            raise credentials_exception

        token_data = schemas.TokenData(id=id)

    except JWTError:
        if raise_on_error:
            raise credentials_exception

        token_data = None

    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), raise_on_error=True, db: Session = Depends(get_db)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f'Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    token = verify_access_token(token, credentials_exception, raise_on_error=raise_on_error)

    user = db.query(User).filter(User.id == token.id).first()

    if not user:
        raise HTTPException(credentials_exception)

    return user


def is_teacher_or_error(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    if user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail='Only teacher authorized to access this endpoint')

    return user


def get_current_user_socket(token: str):
    user = None

    try:
        if 'Bearer' in token:
            token = token.split('Bearer ')[1]
        token = verify_access_token(token=token, credentials_exception=None, raise_on_error=False)

        user = session_db.query(User).filter(User.id == token.id).first()

        return user

    except:
        ...

    return user
