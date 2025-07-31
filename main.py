from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Optional

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


class OlympsBase(BaseModel):
    name: str
    profile: str
    level: int  # 1,2,3, 0-не рсош
    user_tg_id: int
    result: int  # 0-победитель, 1-призер, 2-финалист, 3-участник
    year: str
    is_approved: bool



class UsersBase(BaseModel):
    tg_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    phone_verified: Optional[bool] = False  # поле для верификации телефона
    age: Optional[int] = None
    city: Optional[str] = None
    status: Optional[int] = None  # 0-свободен / 1-в отношениях
    goal: Optional[int] = (
        None  # 0-совместный бот, 1-общение, 2-поиск команды, 3-отношения
    )
    who_interested: Optional[int] = None  # 0-ж / 1-м / 2-все
    date_of_birth: Optional[str] = (
        None  # дата рождения пользователя (в формате ДД-ММ-ГГГГ)
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/olymp/{user_tg_id}")
async def get_olymps(user_tg_id: int, db: db_dependency):
    result = db.query(models.Olymps).filter(models.Olymps.user_tg_id == user_tg_id).all()
    if not result:
        raise HTTPException(status_code=404, detail="Olymp is not found")
    return result


@app.post("/olymp/create/")
async def create_olymp(olymp: OlympsBase, db: db_dependency):
    """
    Создаёт новую запись олимпиады на основе переданных данных.
    Принимает объект OlympsBase, сохраняет его в базе данных и возвращает созданную запись.
    """
    db_olymp = models.Olymps(
        name=olymp.name,
        profile=olymp.profile,
        level=olymp.level,
        user_tg_id=olymp.user_tg_id,
        result=olymp.result,
        year=olymp.year,
        is_approved=olymp.is_approved,
    )
    db.add(db_olymp)
    db.commit()
    db.refresh(db_olymp)
    return db_olymp


@app.delete("/olymp/delete/{olymp_id}")
async def delete_olymp(olymp_id: int, db: db_dependency):
    """
    Удаляет олимпиаду по заданному идентификатору olymp_id.
    Если олимпиада с таким id не найдена, возвращает ошибку 404.
    В случае успешного удаления возвращает сообщение с подтверждением.
    """
    olymp = db.query(models.Olymps).filter(models.Olymps.id == olymp_id).first()
    if not olymp:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")
    db.delete(olymp)
    db.commit()
    return {"detail": f"Олимпиада с id {olymp_id} успешно удалена"}


@app.post("/user/create/")
async def create_user(tg_id: int, db: db_dependency):
    """
    Создаёт нового пользователя по tg_id.
    Если пользователь с таким tg_id уже существует, возвращает ошибку.
    """
    existing_user = db.query(models.Users).filter(models.Users.tg_id == tg_id).first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким tg_id уже существует"
        )
    new_user = models.Users(tg_id=tg_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "status": "OK",
    }


@app.get("/user/get/{tg_id}")
async def get_user(tg_id: int, db: db_dependency):
    """
    Ищет пользователя по tg_id, если находит, то возвращает все поля.
    Иначе выводит ошибку
    """
    result = db.query(models.Users).filter(models.Users.tg_id == tg_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User is not found")
    return result


@app.put("/user/update/", response_model=UsersBase)
async def update_user(user: UsersBase, db: db_dependency):
    """
    Обновляет пользователя по tg_id.
    Если пользователь найден, обновляет только те поля, которые не равны None в запросе.
    Если пользователь не найден, возвращает ошибку.
    """
    existing_user = (
        db.query(models.Users).filter(models.Users.tg_id == user.tg_id).first()
    )
    if not existing_user:
        raise HTTPException(
            status_code=404, detail="Пользователь с таким tg_id не найден"
        )
    # Обновляем только те поля, которые не None
    update_fields = [
        "first_name",
        "last_name",
        "middle_name",
        "phone",
        "phone_verified",
        "age",
        "city",
        "status",
        "goal",
        "who_interested",
        "date_of_birth",
    ]
    for field in update_fields:
        value = getattr(user, field)
        if value is not None:
            setattr(existing_user, field, value)
    db.commit()
    db.refresh(existing_user)
    return user

@app.delete("/user/delete/{user_tg_id}")
async def delete_user(user_tg_id: int, db: db_dependency):
    """
    Удаляет пользователя по tg_id.
    Если пользователь найден, удаляет его из базы данных.
    Если пользователь не найден, возвращает ошибку 404.
    """
    user = db.query(models.Users).filter(models.Users.tg_id == user_tg_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"detail": f"Пользователь с tg_id {user_tg_id} успешно удален"}