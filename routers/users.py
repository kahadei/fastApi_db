from datetime import timedelta, datetime
from typing import Annotated

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from database import SessionLocal
from models import Users, ToDo
from .auth import get_current_user


router = APIRouter(
    prefix='/user',
    tags=['user']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependecy = Annotated[dict, Depends(get_current_user)]


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class UserVerif(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


@router.get('/', status_code=status.HTTP_200_OK)
async def get_user(user: user_dependecy, db: db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail='Unauthorized')
    return db.query(Users).filter(Users.id == user.get('id')).first()


@router.put('/passsword', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependecy, db: db_dependency, user_verif: UserVerif):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')

    user = db.query(Users).filter(Users.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verif.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Unauthorized')
    user.hashed_password = bcrypt_context.hash(user_verif.new_password)
    db.add(user)
    db.commit()
