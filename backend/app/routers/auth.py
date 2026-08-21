from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import create_access_token, current_user, optional_current_user, verify_password
from ..db.database import get_db
from ..db.models import User
from ..schemas import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def ser(user: User):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.strip().lower())).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": ser(user)}


@router.get("/session")
def session(user: User | None = Depends(optional_current_user)):
    return {"authenticated": bool(user), "user": ser(user) if user else None}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return ser(user)
