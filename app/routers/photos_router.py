import os
import uuid
import pathlib

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, Photo
from ..schemas import PhotoOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/photos", tags=["photos"])

UPLOAD_DIR = pathlib.Path(os.getenv("UPLOAD_DIR", "/uploads"))
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PHOTOS = 6


@router.post("/", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Maak eerst een profiel aan")

    existing_count = db.query(Photo).filter(Photo.profile_id == profile.id).count()
    if existing_count >= MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"Maximaal {MAX_PHOTOS} foto's toegestaan")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Alleen JPG, PNG, WebP of GIF toegestaan")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Bestand mag max 10 MB zijn")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"

    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    filepath = user_dir / filename
    filepath.write_bytes(contents)

    photo = Photo(
        profile_id=profile.id,
        filename=f"{current_user.id}/{filename}",
        position=existing_count,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return PhotoOut(
        id=photo.id,
        filename=photo.filename,
        url=f"/uploads/{photo.filename}",
        position=photo.position,
    )


@router.delete("/{photo_id}", status_code=status.HTTP_200_OK)
def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profiel niet gevonden")

    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.profile_id == profile.id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto niet gevonden")

    # Delete file
    filepath = UPLOAD_DIR / photo.filename
    if filepath.exists():
        filepath.unlink()

    db.delete(photo)
    db.commit()

    # Reorder remaining photos
    remaining = db.query(Photo).filter(Photo.profile_id == profile.id).order_by(Photo.position).all()
    for i, p in enumerate(remaining):
        p.position = i
    db.commit()

    return {"detail": "Foto verwijderd"}


@router.get("/user/{user_id}", response_model=list[PhotoOut])
def get_user_photos(
    user_id: str,
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profiel niet gevonden")

    photos = db.query(Photo).filter(Photo.profile_id == profile.id).order_by(Photo.position).all()
    return [
        PhotoOut(id=p.id, filename=p.filename, url=f"/uploads/{p.filename}", position=p.position)
        for p in photos
    ]
