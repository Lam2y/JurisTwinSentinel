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
from ..db.models import User, RolePolicy

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 180_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, expected = encoded.split("$", 2)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 180_000).hex()
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id), "email": user.email, "role": user.role, "name": user.name,
        "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    settings = get_settings()
    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except Exception:
        user = None
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    policy = db.execute(select(RolePolicy).where(RolePolicy.role == user.role)).scalar_one_or_none()
    if policy and not policy.enabled:
        raise HTTPException(status_code=403, detail=f"Role '{user.role}' is disabled by RBAC policy")
    return user


def require_roles(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role '{user.role}' is not allowed")
        return user
    return dep


def require_capability(capability: str):
    def dep(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
        policy = db.execute(select(RolePolicy).where(RolePolicy.role == user.role)).scalar_one_or_none()
        if not policy or not bool(getattr(policy, capability, False)):
            raise HTTPException(status_code=403, detail=f"Role '{user.role}' lacks capability '{capability}'")
        return user
    return dep
