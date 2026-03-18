from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, Photo
from ..schemas import ProfileCreate, ProfileUpdate, ProfileOut, PhotoOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def _enrich_profile(profile: Profile) -> ProfileOut:
    """Add photo URLs to a profile."""
    photos = [
        PhotoOut(id=p.id, filename=p.filename, url=f"/uploads/{p.filename}", position=p.position)
        for p in (profile.photos or [])
    ]
    out = ProfileOut.model_validate(profile)
    out.photos = photos
    return out


@router.post("/", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profiel bestaat al")

    profile = Profile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _enrich_profile(profile)


@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profiel niet gevonden")
    return _enrich_profile(profile)


@router.patch("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profiel niet gevonden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return _enrich_profile(profile)


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: UUID,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profiel niet gevonden")
    return _enrich_profile(profile)


@router.get("/", response_model=list[ProfileOut])
def discover(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return profiles the current user has NOT yet swiped on."""
    from ..models import Swipe

    swiped_ids = (
        db.query(Swipe.swiped_id)
        .filter(Swipe.swiper_id == current_user.id)
        .subquery()
    )

    profiles = (
        db.query(Profile)
        .filter(
            Profile.user_id != current_user.id,
            Profile.user_id.notin_(swiped_ids),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_enrich_profile(p) for p in profiles]
