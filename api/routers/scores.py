"""
routers/scores.py
-----------------
Score submission and leaderboard endpoints.

GET  /scores/leaderboard  — public top-10 global scores
POST /scores/submit       — authenticated score submission with HMAC check
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db, Score, User
from auth import get_current_user
from security import verify_digest

router  = APIRouter(prefix="/scores", tags=["scores"])
limiter = Limiter(key_func=get_remote_address)


class ScoreSubmission(BaseModel):
    score:      int   = Field(ge=0)
    duration_s: float = Field(ge=0.0)
    hmac:       str


class LeaderboardEntry(BaseModel):
    rank:         int
    username:     str
    score:        int
    duration_s:   float
    submitted_at: datetime

    class Config:
        from_attributes = True


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    """Return the top-10 all-time scores.

    Public endpoint — no authentication required.

    Returns:
        List of up to 10 LeaderboardEntry objects ordered by score descending.
    """
    rows = (
        db.query(Score, User.username)
        .join(User)
        .order_by(Score.score.desc())
        .limit(10)
        .all()
    )
    return [
        LeaderboardEntry(
            rank=i + 1,
            username=row.username,
            score=row.Score.score,
            duration_s=row.Score.duration_s,
            submitted_at=row.Score.submitted_at,
        )
        for i, row in enumerate(rows)
    ]


@router.post("/submit", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def submit_score(
    request: Request,
    body:    ScoreSubmission,
    db:      Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a score for the authenticated player.

    Rate-limited to 10 submissions per minute per IP.
    The HMAC digest is verified before persisting the score.

    Args:
        body: Score value, session duration, and HMAC digest.

    Raises:
        HTTPException 403 if the HMAC digest is invalid.
    """
    if not verify_digest(current_user.username, body.score, body.duration_s, body.hmac):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid score signature — submission rejected",
        )

    entry = Score(
        user_id=current_user.id,
        score=body.score,
        duration_s=body.duration_s,
        hmac_digest=body.hmac,
    )
    db.add(entry)
    db.commit()
    return {"message": "Score submitted", "score": body.score}
