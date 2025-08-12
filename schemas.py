from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class OlympsBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    profile: str = Field(min_length=1, max_length=255)
    level: int = Field(ge=0, le=3)
    user_tg_id: str = Field(min_length=1, max_length=64)
    result: int = Field(ge=0, le=3)
    year: str = Field(min_length=4, max_length=10)
    is_approved: Optional[bool] = None
    is_displayed: Optional[bool] = None


class UsersBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tg_id: str = Field(min_length=1, max_length=64)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=32)
    phone_verified: Optional[bool] = False
    age: Optional[int] = Field(default=None, ge=0, le=150)
    city: Optional[str] = Field(default=None, max_length=100)
    status: Optional[int] = Field(default=None, ge=0, le=1)
    goal: Optional[int] = Field(default=None, ge=0, le=3)
    who_interested: Optional[int] = Field(default=None, ge=0, le=2)
    date_of_birth: Optional[str] = Field(default=None, max_length=20)
    face_photo_id: Optional[str] = Field(default=None, max_length=200)
    photo_id: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    gender: Optional[bool] = None  # False=male, True=female


class LikesBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_user_tg_id: str = Field(min_length=1, max_length=64)
    to_user_tg_id: str = Field(min_length=1, max_length=64)
    text: Optional[str] = Field(default=None, max_length=1000)
    is_like: bool
    is_readed: Optional[bool] = False

    @field_validator("to_user_tg_id")
    @classmethod
    def validate_distinct_users(cls, to_user_tg_id: str, info):
        from_user_tg_id = info.data.get("from_user_tg_id")
        if from_user_tg_id and from_user_tg_id == to_user_tg_id:
            raise ValueError("from_user_tg_id and to_user_tg_id must be different")
        return to_user_tg_id