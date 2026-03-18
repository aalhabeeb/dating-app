from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Profile, Swipe, Match, SwipeAction
from ..schemas import SwipeCreate, SwipeOut, MatchOut, ProfileOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.post("/swipe", response_model=SwipeOut, status_code=status.HTTP_201_CREATED)
def swipe(
    payload: SwipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.swiped_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Je kunt niet op jezelf swipen")

    # Check target user exists
    target = db.query(User).filter(User.id == payload.swiped_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gebruiker niet gevonden")

    # Prevent duplicate swipes
    existing = (
        db.query(Swipe)
        .filter(Swipe.swiper_id == current_user.id, Swipe.swiped_id == payload.swiped_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Je hebt al geswiped op deze gebruiker")

    swipe_obj = Swipe(
        swiper_id=current_user.id,
        swiped_id=payload.swiped_id,
        action=payload.action,
    )
    db.add(swipe_obj)

    # Check for mutual like → create match
    if payload.action == SwipeAction.like:
        mutual = (
            db.query(Swipe)
            .filter(
                Swipe.swiper_id == payload.swiped_id,
                Swipe.swiped_id == current_user.id,
                Swipe.action == SwipeAction.like,
            )
            .first()
        )
        if mutual:
            # Order IDs consistently so the unique constraint works
            id1, id2 = sorted([current_user.id, payload.swiped_id])
            match_obj = Match(user1_id=id1, user2_id=id2)
            db.add(match_obj)

    db.commit()
    db.refresh(swipe_obj)
    return swipe_obj


@router.get("/", response_model=list[MatchOut])
def get_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .filter((Match.user1_id == current_user.id) | (Match.user2_id == current_user.id))
        .all()
    )

    result = []
    for m in matches:
        other_id = m.user2_id if m.user1_id == current_user.id else m.user1_id
        other_profile = db.query(Profile).filter(Profile.user_id == other_id).first()
        if other_profile:
            result.append(
                MatchOut(
                    id=m.id,
                    user1_id=m.user1_id,
                    user2_id=m.user2_id,
                    matched_profile=ProfileOut.model_validate(other_profile),
                    created_at=m.created_at,
                )
            )
    return result
