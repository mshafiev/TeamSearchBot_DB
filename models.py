from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from database import Base
import uuid


def generate_uuid_str() -> str:
    return str(uuid.uuid4())


class Olymps(Base):
    __tablename__ = "olymps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    profile = Column(String, nullable=False)
    level = Column(Integer, default=0)  # 1,2,3, 0-не рсош
    user_tg_id = Column(String, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    result = Column(
        Integer, nullable=False
    )  # 0-победитель, 1-призер, 2-финалист, 3-участник
    year = Column(String, nullable=False)
    is_approved = Column(Boolean, default=False)
    is_displayed = Column(Boolean, default=False)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    status = Column(Integer, nullable=True)  # 0-свободен / 1-в отношениях
    goal = Column(
        Integer, nullable=True
    )  # 0-совместный бот, 1-общение, 2-поиск команды, 3-отношения
    who_interested = Column(Integer, nullable=True)  # 0-ж / 1-м / 2-все
    date_of_birth = Column(
        String, nullable=True
    )  # дата рождения пользователя (в формате ДД-ММ-ГГГГ)
    face_photo_id = Column(String, nullable=True)
    photo_id = Column(String, nullable=True)
    description = Column(String, nullable=True)
    gender = Column(Boolean, nullable=True) # 0m 1g


class Likes(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    from_user_tg_id = Column(String, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    to_user_tg_id = Column(String, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=True)
    is_like = Column(Boolean, nullable=False)
    is_readed = Column(Boolean, default=False)
