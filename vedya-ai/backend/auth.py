"""
Auth security for VedyaAI.

Tools / mechanisms:
- bcrypt (via passlib) — one-way password hashing (never store plaintext)
- JWT (PyJWT, HS256) — short-lived bearer tokens for API auth
- FastAPI Depends — request-scoped identity extraction
- Optional auth — guests can still use recommend; conversations require login
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

JWT_SECRET = os.getenv("JWT_SECRET", "vedya-dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=120)
    preferred_locale: str = Field("en", pattern="^(en|hi|gu)$")


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    user_id: str
    email: str
    display_name: Optional[str] = None
    preferred_locale: str = "en"
    role: str = "user"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str, email: str, role: str = "user") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRE_HOURS),
        "iss": "vedyaai",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], issuer="vedyaai")
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_signup(req: SignupRequest) -> None:
    if not EMAIL_RE.match(req.email.strip()):
        raise HTTPException(status_code=400, detail="Invalid email address")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if req.password.lower() in {req.email.lower(), "password", "12345678"}:
        raise HTTPException(status_code=400, detail="Password is too weak")


def fetch_user_by_email(db, email: str) -> Optional[dict[str, Any]]:
    cur = db.cursor()
    cur.execute(
        """
        SELECT user_id::text, email, password_hash, display_name, preferred_locale, is_active, role
        FROM users WHERE lower(email) = lower(%s)
        """,
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "display_name": row[3],
        "preferred_locale": row[4],
        "is_active": row[5],
        "role": row[6],
    }


def fetch_user_by_id(db, user_id: str) -> Optional[dict[str, Any]]:
    cur = db.cursor()
    cur.execute(
        """
        SELECT user_id::text, email, display_name, preferred_locale, is_active, role
        FROM users WHERE user_id = %s
        """,
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "email": row[1],
        "display_name": row[2],
        "preferred_locale": row[3],
        "is_active": row[4],
        "role": row[5],
    }


def create_user(db, req: SignupRequest) -> AuthUser:
    validate_signup(req)
    email = normalize_email(req.email)
    if fetch_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered")

    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, display_name, preferred_locale)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id::text, email, display_name, preferred_locale, role
            """,
            (email, hash_password(req.password), req.display_name, req.preferred_locale),
        )
        row = cur.fetchone()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()

    return AuthUser(
        user_id=row[0],
        email=row[1],
        display_name=row[2],
        preferred_locale=row[3],
        role=row[4] or "user",
    )


def authenticate_user(db, req: LoginRequest) -> AuthUser:
    user = fetch_user_by_email(db, normalize_email(req.email))
    # Constant-ish failure message to reduce account enumeration
    if not user or not user["is_active"] or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    cur = db.cursor()
    cur.execute("UPDATE users SET last_login_at = NOW() WHERE user_id = %s", (user["user_id"],))
    db.commit()
    cur.close()

    return AuthUser(
        user_id=user["user_id"],
        email=user["email"],
        display_name=user["display_name"],
        preferred_locale=user["preferred_locale"],
        role=user.get("role", "user"),
    )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AuthUser]:
    """Attach user if Bearer token present; otherwise None (guest)."""
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    # Lazy DB lookup deferred to route via user_id in token for speed;
    # routes that need full profile should re-fetch.
    return AuthUser(
        user_id=str(payload["sub"]),
        email=str(payload.get("email", "")),
        preferred_locale="en",
        role=str(payload.get("role", "user")),
    )


def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(credentials.credentials)
    return AuthUser(
        user_id=str(payload["sub"]),
        email=str(payload.get("email", "")),
        preferred_locale="en",
        role=str(payload.get("role", "user")),
    )


def require_admin(user: AuthUser = Depends(require_user)) -> AuthUser:
    """Admin-only gate — corpus curators / faculty administrators."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def ensure_uuid(value: str, field: str = "id") -> str:
    try:
        return str(UUID(value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc
