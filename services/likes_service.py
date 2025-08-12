from sqlalchemy.orm import Session
from typing import Optional, List
import models
from schemas import LikesBase


def create_like(db: Session, like: LikesBase) -> models.Likes:
    from_user = (
        db.query(models.Users)
        .filter(models.Users.tg_id == like.from_user_tg_id)
        .first()
    )
    to_user = (
        db.query(models.Users)
        .filter(models.Users.tg_id == like.to_user_tg_id)
        .first()
    )
    if not from_user or not to_user:
        raise ValueError("Either from_user or to_user does not exist")

    db_like = models.Likes(
        from_user_tg_id=like.from_user_tg_id,
        to_user_tg_id=like.to_user_tg_id,
        text=like.text,
        is_like=like.is_like,
        is_readed=like.is_readed,
    )
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def get_last_likes(db: Session, user_tg_id: str, count: int) -> List[models.Likes]:
    return (
        db.query(models.Likes)
        .filter(models.Likes.from_user_tg_id == user_tg_id)
        .order_by(models.Likes.id.desc())
        .limit(count)
        .all()
    )


def like_exists(db: Session, from_user_tg_id: str, to_user_tg_id: str, is_like: bool) -> bool:
    like = (
        db.query(models.Likes)
        .filter(
            models.Likes.from_user_tg_id == from_user_tg_id,
            models.Likes.to_user_tg_id == to_user_tg_id,
            models.Likes.is_like == is_like,
        )
        .first()
    )
    return like is not None