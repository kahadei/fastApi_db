from datetime import timedelta, datetime
from typing import Annotated

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from database import SessionLocal
from models import Users, ToDo
from .auth import get_current_user


router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependecy = Annotated[dict, Depends(get_current_user)]


@router.get('/todo', status_code=status.HTTP_200_OK)
async def read_all(user: user_dependecy, db: db_dependency):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail='Unauthorized')
    return db.query(ToDo).all()


@router.delete('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def del_todo(user: user_dependecy, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=401, detail='Unauthorized')
    todo_model = db.query(ToDo).filter(ToDo.id == todo_id)
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')
    todo_model.delete()
    db.commit()
