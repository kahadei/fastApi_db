from typing import Annotated

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from database import engine, SessionLocal
from models import ToDo
from .auth import get_current_user

router = APIRouter()

models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependecy = Annotated[dict, Depends(get_current_user)]


class ToDoRequest(BaseModel):
    title: str = Field(min_length=4)
    description: str = Field(min_length=4, max_length=200)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.get('/', response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(models.ToDo).filter(models.ToDo.owner_id == user.get('id')).all()
    return templates.TemplateResponse('home.html', {"request": request, "todos": todos, "user": user})


@router.get('/add-todo', response_class=HTMLResponse)
async def add_new_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('add-todo.html', {"request": request, "user": user})


@router.post('/add-todo', response_class=HTMLResponse)
async def create_todo(request: Request,
                      title: str = Form(...),
                      description: str = Form(...),
                      priority: int = Form(...),
                      db: Session = Depends(get_db)
                      ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.ToDo()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get('id')
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo(request: Request,
                    todo_id: int,
                    db: Session = Depends(get_db)
                    ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    return templates.TemplateResponse('edit-todo.html', {"request": request, "todo": todo, "user": user})


@router.post('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo_commit(request: Request,
                           todo_id: int,
                           title: str = Form(...),
                           description: str = Form(...),
                           priority: int = Form(...),
                           db: Session = Depends(get_db)
                           ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    todo.title = title
    todo.description = description
    todo.priority = priority
    todo.complete = False
    todo.owner_id = 6
    db.add(todo)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get('/del-todo/{todo_id}', response_class=HTMLResponse)
async def delete_todo(request: Request,
                      todo_id: int,
                      db: Session = Depends(get_db)
                      ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.ToDo).filter(models.ToDo.owner_id == user.get('id')).filter(models.ToDo.id == todo_id).first()
    if todo is None:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    db.query(models.ToDo).filter(models.ToDo.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get('/complete/{todo_id}', response_class=HTMLResponse)
async def complete_todo(request: Request,
                        todo_id: int,
                        db: Session = Depends(get_db)
                        ):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.ToDo).filter(models.ToDo.owner_id == 6).filter(models.ToDo.id == todo_id).first()
    todo.complete = not todo.complete
    db.add(todo)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@router.get("/todos")
async def all_todos(user: user_dependecy, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Not allow')

    return db.query(ToDo).filter(ToDo.owner == user.get('id')).all()


@router.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependecy, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')

    todo_qs = db.query(ToDo).filter(ToDo.owner == user.get('id')).filter(ToDo.id == todo_id).first()
    if todo_qs is not None:
        return todo_qs
    raise HTTPException(status_code=404, detail='Not found')


@router.post('/todo/new_todo', status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependecy, db: db_dependency, todo_request: ToDoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')
    todo_model = ToDo(**todo_request.model_dump(), owner=user.get('id'))
    db.add(todo_model)
    db.commit()


@router.put('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependecy,
                      db: db_dependency,
                      todo_request: ToDoRequest,
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')

    todo_model = db.query(ToDo).filter(ToDo.owner == user.get('id')).filter(ToDo.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    db.add(todo_model)
    db.commit()


@router.delete('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
async def del_todo(user: user_dependecy,
                   db: db_dependency,
                   todo_id: int = Path(gt=0)
                   ):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')

    todo_model = db.query(ToDo).filter(ToDo.owner == user.get('id')).filter(ToDo.id == todo_id)
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')
    todo_model.delete()
    db.commit()
