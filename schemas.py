from pydantic import BaseModel, Field, field_validator
from typing import Optional


class OlympCreate(BaseModel):
    name: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    level: int = Field(ge=0)
    user_tg_id: int = Field(gt=0)
    result: int = Field(ge=0)
    year: str = Field(min_length=1)
    is_approved: Optional[bool] = None
    is_displayed: Optional[bool] = None


class UserCreate(BaseModel):
    tg_id: int = Field(gt=0)


class UserUpdate(BaseModel):
    tg_id: int = Field(gt=0)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    phone_verified: Optional[bool] = False
    age: Optional[int] = Field(default=None, ge=0)
    city: Optional[str] = None
    status: Optional[int] = Field(default=None, ge=0)
    goal: Optional[int] = Field(default=None, ge=0)
    who_interested: Optional[int] = Field(default=None, ge=0)
    date_of_birth: Optional[str] = None
    face_photo_id: Optional[str] = None
    photo_id: Optional[str] = None
    description: Optional[str] = None
    gender: Optional[bool] = None


class LikeCreate(BaseModel):
    from_user_tg_id: int = Field(gt=0)
    to_user_tg_id: int = Field(gt=0)
    text: Optional[str] = None
    is_like: bool
    is_readed: Optional[bool] = False

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        return stripped if stripped else None