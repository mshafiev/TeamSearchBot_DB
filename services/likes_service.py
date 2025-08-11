from sqlalchemy.orm import Session
from typing import Optional
from schemas import LikeCreate
import models


def create_like_record(db: Session, like: LikeCreate) -> models.Likes:
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
        raise ValueError("One of the users was not found")

    like_row = models.Likes(
        from_user_tg_id=like.from_user_tg_id,
        to_user_tg_id=like.to_user_tg_id,
        text=like.text,
        is_like=like.is_like,
        is_readed=like.is_readed,
    )
    db.add(like_row)
    db.commit()
    db.refresh(like_row)
    return like_row