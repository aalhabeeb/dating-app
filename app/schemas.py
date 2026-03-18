from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .models import Gender, SwipeAction


# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Profile ───────────────────────────────────────────
class ProfileCreate(BaseModel):
    display_name: str = Field(max_length=100)
    age: int = Field(ge=18, le=120)
    gender: Gender
    bio: str = Field(default="", max_length=2000)
    photo_url: str = Field(default="", max_length=500)
    city: str = Field(default="", max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    gender: Optional[Gender] = None
    bio: Optional[str] = Field(default=None, max_length=2000)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    age: int
    gender: Gender
    bio: str
    photo_url: str
    city: str
    photos: list["PhotoOut"] = []
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Photos ────────────────────────────────────────────
class PhotoOut(BaseModel):
    id: UUID
    filename: str
    url: str = ""
    position: int

    model_config = {"from_attributes": True}


# ── Swipe / Match ────────────────────────────────────
class SwipeCreate(BaseModel):
    swiped_id: UUID
    action: SwipeAction


class SwipeOut(BaseModel):
    id: UUID
    swiper_id: UUID
    swiped_id: UUID
    action: SwipeAction
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchOut(BaseModel):
    id: UUID
    user1_id: UUID
    user2_id: UUID
    matched_profile: ProfileOut
    created_at: datetime

    model_config = {"from_attributes": True}
