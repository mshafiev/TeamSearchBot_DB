from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Optional
from logger import logger, validation_exception_handler, http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from schemas import OlympsBase, UsersBase, LikesBase
from services.likes_service import create_like as service_create_like, get_last_likes as service_get_last_likes, like_exists as service_like_exists


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
logger.info("Application startup: tables ensured and exception handlers registered")

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# короткоживущая сессия БД на каждый запрос

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()







@app.get("/olymp/{user_tg_id}")
async def get_user_olymps(user_tg_id: str, db: Session = Depends(get_db)):
    """
    Получить все олимпиады пользователя по его user_tg_id.

    Аргументы:
        user_tg_id (str): Telegram ID пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        Список олимпиад пользователя.

    Исключения:
        404: Если олимпиады не найдены.
    """
    result = (
        db.query(models.Olymps).filter(models.Olymps.user_tg_id == user_tg_id).all()
    )
    if not result:
        logger.warning(f"Ошибка Olymp is not found")
        raise HTTPException(status_code=404, detail="Olymp is not found")
    return result


@app.post("/olymp/create/")
async def create_olymp(olymp: OlympsBase, db: Session = Depends(get_db)):
    """
    Создать новую запись олимпиады.

    Аргументы:
        olymp (OlympsBase): Данные олимпиады.
        db (Session): Сессия базы данных.

    Возвращает:
        Созданная запись олимпиады или сообщение об ошибке, если запись уже существует.
    """
    user = db.query(models.Users).filter(models.Users.tg_id == olymp.user_tg_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User is not found")
    
    existing_olymp = db.query(models.Olymps).filter(
        models.Olymps.name == olymp.name,
        models.Olymps.profile == olymp.profile,
        models.Olymps.level == olymp.level,
        models.Olymps.user_tg_id == olymp.user_tg_id,
        models.Olymps.result == olymp.result,
        models.Olymps.year == olymp.year,
    ).first()

    if existing_olymp:
        raise HTTPException(status_code=400, detail="Olympiad already exists with the same data")
    
    db_olymp = models.Olymps(
        name=olymp.name,
        profile=olymp.profile,
        level=olymp.level,
        user_tg_id=olymp.user_tg_id,
        result=olymp.result,
        year=olymp.year,
        is_approved=olymp.is_approved,
        is_displayed=olymp.is_displayed,
    )
    db.add(db_olymp)
    db.commit()
    db.refresh(db_olymp)
    return db_olymp


@app.post("/olymp/set_display/")
async def set_olymp_display(olymp_id: int, db: Session = Depends(get_db)):
    """
    Установить флаг отображения олимпиады (is_displayed).

    Аргументы:
        olymp (OlympsBase): Данные олимпиады (используются user_tg_id, name, year, profile, is_displayed).
        db (Session): Сессия базы данных.

    Возвращает:
        Обновлённая запись олимпиады.

    Исключения:
        404: Если олимпиада не найдена.
    """
    existing_olymp = (
        db.query(models.Olymps)
        .filter(
            models.Olymps.id == olymp_id,
        )
        .first()
    )
    if not existing_olymp:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")
    existing_olymp.is_displayed = not existing_olymp.is_displayed
    db.commit()
    db.refresh(existing_olymp)
    return existing_olymp


@app.delete("/olymp/delete/{olymp_id}")
async def delete_olymp(olymp_id: int, db: Session = Depends(get_db)):
    """
    Удалить олимпиаду по её идентификатору.

    Аргументы:
        olymp_id (str): ID олимпиады.
        db (Session): Сессия базы данных.

    Возвращает:
        Сообщение об успешном удалении.

    Исключения:
        404: Если олимпиада не найдена.
    """
    olymp = db.query(models.Olymps).filter(models.Olymps.id == olymp_id).first()
    if not olymp:
        raise HTTPException(status_code=404, detail="Олимпиада не найдена")
    db.delete(olymp)
    db.commit()
    return {"detail": f"Олимпиада с id {olymp_id} успешно удалена"}


@app.post("/user/create/")
async def create_user(tg_id: str, db: Session = Depends(get_db)):
    """
    Создать нового пользователя по tg_id.

    Аргументы:
        tg_id (int): Telegram ID пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        Статус создания пользователя.

    Исключения:
        400: Если пользователь с таким tg_id уже существует.
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
async def get_user(tg_id: str, db: Session = Depends(get_db)):
    """
    Получить пользователя по tg_id вместе с его олимпиадами.

    Аргументы:
        tg_id (int): Telegram ID пользователя.

    Возвращает:
        Данные пользователя с полем olymps (массив его олимпиад).
    """
    user = db.query(models.Users).filter(models.Users.tg_id == tg_id).first()
    if not user:
        return None
    olymps = db.query(models.Olymps).filter(models.Olymps.user_tg_id == tg_id).all()
    user_data = user.__dict__.copy()
    user_data["olymps"] = [olymp.__dict__ for olymp in olymps]
    return user_data



@app.put("/user/update/", response_model=UsersBase)
async def update_user(user: UsersBase, db: Session = Depends(get_db)):
    """
    Обновить данные пользователя по tg_id.

    Аргументы:
        user (UsersBase): Данные пользователя для обновления.
        db (Session): Сессия базы данных.

    Возвращает:
        Обновлённые данные пользователя (только те поля, которые были переданы).

    Исключения:
        404: Если пользователь не найден.
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
        "username",
        "age",
        "city",
        "status",
        "goal",
        "who_interested",
        "date_of_birth",
        "face_photo_id",
        "photo_id",
        "description",
        "gender"
    ]
    for field in update_fields:
        value = getattr(user, field)
        if value is not None:
            setattr(existing_user, field, value)
    db.commit()
    db.refresh(existing_user)
    return user


@app.delete("/user/delete/{user_tg_id}")
async def delete_user(user_tg_id: str, db: Session = Depends(get_db)):
    """
    Удалить пользователя по tg_id.

    Аргументы:
        user_tg_id (int): Telegram ID пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        Сообщение об успешном удалении.

    Исключения:
        404: Если пользователь не найден.
    """
    user = db.query(models.Users).filter(models.Users.tg_id == user_tg_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"detail": f"Пользователь с tg_id {user_tg_id} успешно удален"}


@app.post("/like/create/")
async def create_like(like: LikesBase, db: Session = Depends(get_db)):
    """
    Создать новый лайк.

    Аргументы:
        like (LikesBase): Данные лайка.
        db (Session): Сессия базы данных.

    Возвращает:
        Созданная запись лайка.
    """
    try:
        created = service_create_like(db, like)
        return created
    except ValueError as ve:
        logger.warning(f"Ошибка создания лайка: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Не удалось создать лайк")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/like/delete/")
async def delete_like(id: int, db: Session = Depends(get_db)):
    """
    Удалить лайк по id

    Аргументы:
        id (str): id лайка
        db (Session): Сессия базы данных.

    Возвращает:
        Сообщение об успешном удалении.

    Исключения:
        404: Если лайк не найден.
    """
    like = (
        db.query(models.Likes)
        .filter(
            models.Likes.id == id,
        )
        .first()
    )
    if not like:
        raise HTTPException(status_code=404, detail="Лайк не найден")
    db.delete(like)
    db.commit()
    return {"detail": f"Like with id {id} was deleted"}


@app.patch("/like/set_read/")
async def set_like_readed(from_user_tg_id: str, to_user_tg_id: str, db: Session = Depends(get_db)):
    """
    Изменить статус "прочитано" у лайка.

    Аргументы:
        from_user_tg_id (int): Telegram ID пользователя, который поставил лайк.
        to_user_tg_id (int): Telegram ID пользователя, которому поставлен лайк.
        db (Session): Сессия базы данных.

    Возвращает:
        Обновленная запись лайка.

    Исключения:
        404: Если лайк не найден.
    """
    likes = (
        db.query(models.Likes)
        .filter(
            models.Likes.from_user_tg_id == from_user_tg_id,
            models.Likes.to_user_tg_id == to_user_tg_id,
        )
        .order_by(models.Likes.id.desc())
        .all()
    )
    if not likes:
        raise HTTPException(status_code=404, detail="Лайк не найден")
    for like in likes:
        like.is_readed = True
        db.commit()
        db.refresh(like)
    return likes


@app.get("/like/get_last/")
async def get_last_likes(user_tg_id: str, count: int, db: Session = Depends(get_db)):
    """
    Получить последние X лайков пользователя (кому он понравился).
    """
    try:
        return service_get_last_likes(db, user_tg_id, count)
    except Exception:
        logger.exception("Не удалось получить последние лайки")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/like/get_incoming/")
async def get_incoming_likes(user_tg_id: str, only_unread: bool = True, count: int = 50, db: Session = Depends(get_db)):
    """
    Получить входящие лайки (кому вы понравились).

    Args:
        user_tg_id: TG ID пользователя, которому поставили лайк
        only_unread: вернуть только непросмотренные (is_readed=False)
        count: ограничение количества
    """
    q = db.query(models.Likes).filter(
        models.Likes.to_user_tg_id == user_tg_id,
        models.Likes.is_like == True,
    ).order_by(models.Likes.id.desc())
    if only_unread:
        q = q.filter(models.Likes.is_readed == False)
    return q.limit(count).all()


@app.get("/test/{test}")
async def get_test(test: int):
    return test


@app.get("/users/all")
async def get_all_users(db: Session = Depends(get_db)):
    """
    Получить всех пользователей.

    Возвращает:
        Список всех пользователей из базы данных.
    """
    users = db.query(models.Users).all()
    return users


@app.get("/like/exists/")
async def like_exists(from_user_tg_id: str, to_user_tg_id: str, is_like: bool = True, db: Session = Depends(get_db)):
    try:
        return {"exists": service_like_exists(db, from_user_tg_id, to_user_tg_id, is_like)}
    except Exception:
        logger.exception("Ошибка проверки существования лайка")
        raise HTTPException(status_code=500, detail="Internal Server Error")
