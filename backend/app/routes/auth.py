import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.database.connection import SessionLocal
from backend.app.database.models import Profile, User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=100)
    password: str = Field(min_length=1, max_length=128)


def account_response(user: User) -> dict:
    return {
        "access_token": create_access_token(user.user_id),
        "token_type": "bearer",
        "user": {"user_id": user.user_id, "username": user.username, "email": user.email},
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    username = data.username.strip()
    email = data.email.strip().lower()
    if not username or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid username and email address.")

    db: Session = SessionLocal()
    try:
        user = User(username=username, email=email, password_hash=hash_password(data.password))
        db.add(user)
        db.flush()
        db.add(
            Profile(
                user_id=user.user_id,
                goal="general_fitness",
                experience="beginner",
                training_days=3,
                equipment=["bodyweight"],
                diet_preference="omnivore",
                allergies=[],
                restrictions=[],
                injuries=[],
            )
        )
        db.commit()
        db.refresh(user)
        return account_response(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username or email is already registered.",
        ) from None
    finally:
        db.close()


@router.post("/login")
async def login(data: LoginRequest):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data.email.strip().lower()).first()
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if "$" not in user.password_hash:
            user.password_hash = hash_password(data.password)
            db.commit()
            db.refresh(user)
        return account_response(user)
    finally:
        db.close()


@router.get("/me")
async def read_current_user(user: User = Depends(get_current_user)):
    return {"user_id": user.user_id, "username": user.username, "email": user.email}
