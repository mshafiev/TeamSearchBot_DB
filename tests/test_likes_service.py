import pytest
from sqlalchemy.orm import Session
import models
from services.likes_service import create_like_record
from schemas import LikeCreate


def test_create_like_record_success(db_session: Session):
    db_session.add_all([models.Users(tg_id=10), models.Users(tg_id=20)])
    db_session.commit()

    like = LikeCreate(from_user_tg_id=10, to_user_tg_id=20, text="Hi", is_like=True)
    row = create_like_record(db_session, like)

    assert row.id is not None
    assert row.from_user_tg_id == 10
    assert row.to_user_tg_id == 20
    assert row.text == "Hi"


def test_create_like_record_missing_user(db_session: Session):
    db_session.add(models.Users(tg_id=10))
    db_session.commit()

    like = LikeCreate(from_user_tg_id=10, to_user_tg_id=999, text=None, is_like=True)
    with pytest.raises(ValueError):
        create_like_record(db_session, like)