import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

import enum


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    other = "other"


class SwipeAction(str, enum.Enum):
    like = "like"
    dislike = "dislike"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    swipes_given = relationship("Swipe", foreign_keys="Swipe.swiper_id", back_populates="swiper", cascade="all, delete-orphan")
    swipes_received = relationship("Swipe", foreign_keys="Swipe.swiped_id", back_populates="swiped", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(SAEnum(Gender), nullable=False)
    bio = Column(Text, default="")
    photo_url = Column(String(500), default="")
    city = Column(String(100), default="")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="profile")
    photos = relationship("Photo", back_populates="profile", cascade="all, delete-orphan", order_by="Photo.position")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    profile = relationship("Profile", back_populates="photos")


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("swiper_id", "swiped_id", name="uq_swipe_pair"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    swiper_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    swiped_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(SAEnum(SwipeAction), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    swiper = relationship("User", foreign_keys=[swiper_id], back_populates="swipes_given")
    swiped = relationship("User", foreign_keys=[swiped_id], back_populates="swipes_received")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
