from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from ..db.database import get_db
from ..db.models import RolePolicy, User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, expected = encoded.split("$", 2)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _resolve(creds: HTTPAuthorizationCredentials | None, db: Session):
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, get_settings().SECRET_KEY, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except Exception:
        return None
    if not user or not user.active:
        return None
    policy = db.execute(select(RolePolicy).where(RolePolicy.role == user.role)).scalar_one_or_none()
    if policy and not policy.enabled:
        return None
    return user


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    user = _resolve(creds, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return user


def optional_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    return _resolve(creds, db)


def require_superadmin(user: User = Depends(current_user)) -> User:
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return user
