from fastapi import FastAPI, HTTPException, Depends
from typing import Optional
import models
from database import engine, get_db
from sqlalchemy.orm import Session
from logger import logger, validation_exception_handler, http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from schemas import OlympCreate, UserCreate, UserUpdate, LikeCreate
from messaging import publish_like

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.get("/olymp/{user_tg_id}")
async def get_user_olymps(user_tg_id: int, db: Session = Depends(get_db)):
    """
    Получить все олимпиады пользователя по его user_tg_id.

    Аргументы:
        user_tg_id (int): Telegram ID пользователя.
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
async def create_olymp(olymp: OlympCreate, db: Session = Depends(get_db)):
    """
    Создать новую запись олимпиады.

    Аргументы:
        olymp (OlympCreate): Данные олимпиады.
        db (Session): Сессия базы данных.

    Возвращает:
        Созданная запись олимпиады.
    """
    user = db.query(models.Users).filter(models.Users.tg_id == olymp.user_tg_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User is not found")

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
        olymp_id (int): Идентификатор олимпиады.
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
        olymp_id (int): ID олимпиады.
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
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Создать нового пользователя по tg_id.

    Аргументы:
        user (UserCreate): Данные пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        Статус создания пользователя.

    Исключения:
        400: Если пользователь с таким tg_id уже существует.
    """
    existing_user = db.query(models.Users).filter(models.Users.tg_id == user.tg_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким tg_id уже существует")
    new_user = models.Users(tg_id=user.tg_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "OK"}


@app.get("/user/get/{tg_id}")
async def get_user(tg_id: int, db: Session = Depends(get_db)):
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
    user_data["olymps"] = [
        {k: v for k, v in olymp.__dict__.items() if k != "_sa_instance_state"}
        for olymp in olymps
    ]
    # Remove SQLAlchemy state from user dict as well
    user_data.pop("_sa_instance_state", None)
    return user_data


@app.put("/user/update/")
async def update_user(user: UserUpdate, db: Session = Depends(get_db)):
    """
    Обновить данные пользователя по tg_id.

    Аргументы:
        user (UserUpdate): Данные пользователя для обновления.
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
        "phone_verified",
        "age",
        "city",
        "status",
        "goal",
        "who_interested",
        "date_of_birth",
        "face_photo_id",
        "photo_id",
        "description",
        "gender",
    ]
    for field in update_fields:
        value = getattr(user, field)
        if value is not None:
            setattr(existing_user, field, value)
    db.commit()
    db.refresh(existing_user)
    return user


@app.delete("/user/delete/{user_tg_id}")
async def delete_user(user_tg_id: int, db: Session = Depends(get_db)):
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
async def create_like(like: LikeCreate, db: Session = Depends(get_db)):
    """
    Создать новый лайк.

    Аргументы:
        like (LikeCreate): Данные лайка.
        db (Session): Сессия базы данных.

    Возвращает:
        Статус постановки лайка в очередь.
    """
    # Validate users exist to avoid junk in the queue
    from_user = db.query(models.Users).filter(models.Users.tg_id == like.from_user_tg_id).first()
    to_user = db.query(models.Users).filter(models.Users.tg_id == like.to_user_tg_id).first()
    if not from_user or not to_user:
        raise HTTPException(status_code=404, detail="Один из пользователей не найден")

    # Publish for async processing
    try:
        publish_like(like)
        return {"status": "ENQUEUED"}
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение в очередь: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.delete("/like/delete/")
async def delete_like(id: int, db: Session = Depends(get_db)):
    """
    Удалить лайк по id

    Аргументы:
        id (int): id лайка
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
async def set_like_readed(from_user_tg_id: int, to_user_tg_id: int, db: Session = Depends(get_db)):
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
    like = (
        db.query(models.Likes)
        .filter(
            models.Likes.from_user_tg_id == from_user_tg_id,
            models.Likes.to_user_tg_id == to_user_tg_id,
        )
        .order_by(models.Likes.id.desc())
        .first()
    )
    if not like:
        raise HTTPException(status_code=404, detail="Лайк не найден")
    like.is_readed = True
    db.commit()
    db.refresh(like)
    return like


@app.get("/like/get_last/")
async def get_last_likes(user_tg_id: int, count: int, db: Session = Depends(get_db)):
    """
    Получить последние X лайков пользователя.

    Аргументы:
        user_tg_id (int): Telegram ID пользователя, для которого ищем лайки (to_user_tg_id).
        count (int): Количество последних лайков для возврата.
        db (Session): Сессия базы данных.

    Возвращает:
        Список последних лайков (может быть меньше, если лайков меньше чем count).
    """
    likes = (
        db.query(models.Likes)
        .filter(models.Likes.to_user_tg_id == user_tg_id)
        .order_by(models.Likes.id.desc())
        .limit(count)
        .all()
    )
    return likes


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
