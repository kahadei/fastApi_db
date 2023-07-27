from pydantic import BaseModel, Field
from starlette import status

import models
from models import ToDo
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import engine, SessionLocal

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ToDoRequest(BaseModel):
    title: str = Field(min_length=4)
    description: str = Field(min_length=4, max_length=200)
    priority: int = Field(gt=0, lt=6)
    complete: bool


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/todos")
async def root(db: db_dependency):
    return db.query(ToDo).all()


@app.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_qs = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo_qs is not None:
        return todo_qs
    raise HTTPException(status_code=404, detail='Not found')


@app.post('/todo/new_todo', status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: ToDoRequest):
    todo_model = ToDo(**todo_request.model_dump())
    db.add(todo_model)
    db.commit()


@app.put('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,
                      todo_request: ToDoRequest,
                      todo_id: int = Path(gt=0)):
    todo_model = db.query(ToDo).filter(ToDo.id == todo_id).first()
    print(todo_model.id)
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()


@app.delete('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def del_todo(db: db_dependency,
                   todo_id: int = Path(gt=0)
                   ):
    todo_model = db.query(ToDo).filter(ToDo.id == todo_id)
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')
    todo_model.delete()
    db.commit()
