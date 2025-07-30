from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

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
    result: int # 0-победитель, 1-призер, 2-финалист, 3-участник
    year: str

class UsersBase(BaseModel):
    tg_id: int
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    phone: str | None = None
    phone_verified: bool = False  # поле для верификации телефона
    age: int | None = None
    city: str | None = None
    status: int | None = None  # 0-свободен / 1-в отношениях
    goal: int | None = None  # 0-совместный бот, 1-общение, 2-поиск команды, 3-отношения
    who_interested: int | None = None  # 0-ж / 1-м / 2-все
    olymps: List[OlympResultBase]
    date_of_birth: str | None = None  # дата рождения пользователя (в формате ДД-ММ-ГГГГ)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post('/create/olymp/')
async def create_olymp(olymp: OlympsBase, db: db_dependency):
    db_user = models.Olymps(
        name=olymp.name,
        profile=olymp.profile,
        subject=olymp.subject,
        level=olymp.level,
        link=olymp.link
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
