from datetime import timedelta, datetime
from typing import Annotated

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

SECRET_KEY = 'HmLdpkRlMKtQIJg6sjvazXDo78q4ASEf'
ALGORITHM = 'HS256'


class CreateUserRequest(BaseModel):
    id: int = Field()
    email: str = Field()
    username: str = Field()
    first_name: str = Field()
    second_name: str = Field()
    password: str = Field()
    is_active: bool = Field()
    phone_num: str = Field()
    role: str = Field()


class Token(BaseModel):
    access_token: str
    token_type: str


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
    return user


def create_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expire = datetime.utcnow() + expires_delta
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not valid user")
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not valid user")


@router.post('/')
async def create_user(db: db_dependency,
                      user_data: CreateUserRequest):
    user = Users(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        second_name=user_data.second_name,
        role=user_data.role,
        hashed_password=bcrypt_context.hash(user_data.password),
        phone_num=user_data.phone_num,
        is_active=True,
    )

    db.add(user)
    db.commit()


@router.post('/token', response_model=Token)
async def login_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                      db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return 'Failed'
    token = create_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
