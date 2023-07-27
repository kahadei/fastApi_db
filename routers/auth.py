from typing import Annotated

from fastapi import FastAPI, APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return True


class CreateUserRequest(BaseModel):
    id: int = Field()
    email: str = Field()
    username: str = Field()
    first_name: str = Field()
    second_name: str = Field()
    password: str = Field()
    is_active: bool = Field()
    role: str = Field()


@router.post('/auth')
async def create_user(db: db_dependency,
                      user_data: CreateUserRequest):
    user = Users(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        second_name=user_data.second_name,
        role=user_data.role,
        hashed_password=bcrypt_context.hash(user_data.password),
        is_active=True,
    )

    db.add(user)
    db.commit()


@router.post('/token')
async def login_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                      db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return 'Failed'
    return 'Successful'


@router.get('/auth/')
async def get_user():
    return {'user': 'authenticated'}
