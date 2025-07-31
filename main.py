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
    subject: str
    level: int  # 1,2,3, 0-не рсош
    link: str


class OlympResultBase(BaseModel):
    olymp: OlympsBase
    result: int  # 0-победитель, 1-призер, 2-финалист, 3-участник
    year: str
    tg_id: int


class UsersBase(BaseModel):
    tg_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = NoneÒ
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


@app.get("/olymp/{olymp_id}")
async def read_olymp(olymp_id: int, db: db_dependency):
    result = db.query(models.Olymps).filter(models.Olymps.id == olymp_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Olymp is not found")
    return result


@app.post("/olymp/create/")
async def create_olymp(olymp: OlympsBase, db: db_dependency):
    db_olymp = models.Olymps(
        name=olymp.name,
        profile=olymp.profile,
        subject=olymp.subject,
        level=olymp.level,
        link=olymp.link,
    )
    db.add(db_olymp)
    db.commit()
    db.refresh(db_olymp)


@app.delete("/olymp/delete/{olymp_id}")
async def delete_olymp(olymp_id: int, db: db_dependency):
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
        "status": "O",
    }
