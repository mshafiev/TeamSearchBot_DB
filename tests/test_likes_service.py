import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import Base
from services.likes_service import create_like, get_last_likes, like_exists
from schemas import LikesBase


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_user(session, tg_id: str):
    u = models.Users(tg_id=tg_id)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def test_create_and_query_likes(db_session):
    create_user(db_session, "u1")
    create_user(db_session, "u2")

    like = LikesBase(from_user_tg_id="u1", to_user_tg_id="u2", is_like=True)
    created = create_like(db_session, like)

    assert created.id is not None
    assert created.from_user_tg_id == "u1"
    assert created.to_user_tg_id == "u2"

    # exists
    assert like_exists(db_session, "u1", "u2", True) is True
    assert like_exists(db_session, "u1", "u2", False) is False

    # last likes for user2 (incoming)
    results = get_last_likes(db_session, "u2", 10)
    assert len(results) == 1
    assert results[0].id == created.id


def test_create_like_missing_user(db_session):
    create_user(db_session, "u1")
    like = LikesBase(from_user_tg_id="u1", to_user_tg_id="nope", is_like=True)
    with pytest.raises(ValueError):
        create_like(db_session, like)