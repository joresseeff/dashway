"""
routers/auth.py
---------------
Authentication endpoints: register and login.

POST /auth/register  — create a new account
POST /auth/login     — exchange credentials for a JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import get_db, User
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new player account.

    Args:
        body: Username and password.

    Raises:
        HTTPException 409 if the username is already taken.
    """
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    return {"message": f"Account '{body.username}' created successfully"}


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session = Depends(get_db),
):
    """Authenticate and return a JWT bearer token.

    Args:
        form: Standard OAuth2 form with username and password fields.

    Raises:
        HTTPException 401 on invalid credentials.
    """
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
