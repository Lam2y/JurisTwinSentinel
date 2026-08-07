from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import User
from ..schemas import LoginRequest
from ..core.security import verify_password, create_access_token, current_user
from ..services.common import loads

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": serialize_user(user)}

@router.get("/me")
def me(user: User = Depends(current_user)):
    return serialize_user(user)

def serialize_user(user: User):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "assigned_case_refs": loads(user.assigned_case_refs, [])}
