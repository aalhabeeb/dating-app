import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, Swipe, Match
from ..auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Geen admin rechten")
    return current_user


@router.get("/stats")
def get_stats(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {
        "total_users": db.query(User).count(),
        "total_profiles": db.query(Profile).count(),
        "total_swipes": db.query(Swipe).count(),
        "total_likes": db.query(Swipe).filter(Swipe.action == "like").count(),
        "total_dislikes": db.query(Swipe).filter(Swipe.action == "dislike").count(),
        "total_matches": db.query(Match).count(),
    }


@router.get("/users")
def list_users(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    result = []
    for u in users:
        profile = db.query(Profile).filter(Profile.user_id == u.id).first()
        swipes_given = db.query(Swipe).filter(Swipe.swiper_id == u.id).count()
        swipes_received = db.query(Swipe).filter(Swipe.swiped_id == u.id).count()
        matches = db.query(Match).filter((Match.user1_id == u.id) | (Match.user2_id == u.id)).count()
        result.append({
            "id": str(u.id),
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "profile": {
                "display_name": profile.display_name,
                "age": profile.age,
                "gender": profile.gender.value if profile.gender else None,
                "city": profile.city,
                "bio": profile.bio,
            } if profile else None,
            "swipes_given": swipes_given,
            "swipes_received": swipes_received,
            "matches": matches,
        })
    return result


@router.delete("/users/{user_id}")
def delete_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gebruiker niet gevonden")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Je kunt jezelf niet verwijderen")
    db.delete(user)
    db.commit()
    return {"detail": "Gebruiker verwijderd"}


@router.get("/matches")
def list_matches(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    matches = db.query(Match).all()
    result = []
    for m in matches:
        p1 = db.query(Profile).filter(Profile.user_id == m.user1_id).first()
        p2 = db.query(Profile).filter(Profile.user_id == m.user2_id).first()
        result.append({
            "id": str(m.id),
            "user1": p1.display_name if p1 else str(m.user1_id),
            "user2": p2.display_name if p2 else str(m.user2_id),
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return result
