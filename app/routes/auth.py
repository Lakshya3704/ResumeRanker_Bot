"""
auth.py – Authentication routes (signup, login, user profile).

JWT-based authentication with bcrypt password hashing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.models.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.services.database import (
    create_user,
    find_user_by_email,
    verify_password,
    update_login,
    get_user_count,
)
from app.utils.helpers import get_env, setup_logging

logger = setup_logging("drcode.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── JWT config ──
security = HTTPBearer()
JWT_SECRET = get_env("JWT_SECRET", "drcode-super-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


# ──────────────────────────────────────────────
#  JWT helpers
# ──────────────────────────────────────────────

def create_token(email: str) -> str:
    """Create a JWT token for the given email."""
    payload = {
        "sub": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """Decode a JWT token and return the email. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub", "")
        if not email:
            raise HTTPException(401, "Invalid token")
        return email
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency: extract and validate the current user from JWT."""
    email = decode_token(credentials.credentials)
    user = await find_user_by_email(email)
    if not user:
        raise HTTPException(401, "User not found")
    return user


# ──────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
async def signup(body: UserSignupRequest):
    """Register a new user."""
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")

    try:
        user = await create_user(
            name=body.name,
            email=body.email,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(409, str(e))

    token = create_token(body.email)
    logger.info("New signup: %s", body.email)

    return TokenResponse(
        token=token,
        user=UserResponse(
            name=user["name"],
            email=user["email"],
            created_at=str(user["created_at"]),
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest):
    """Authenticate a user and return a JWT."""
    user = await find_user_by_email(body.email)
    if not user:
        raise HTTPException(401, "Invalid email or password.")

    if not verify_password(body.password, user["password"]):
        raise HTTPException(401, "Invalid email or password.")

    await update_login(body.email)
    token = create_token(body.email)
    logger.info("Login: %s", body.email)

    return TokenResponse(
        token=token,
        user=UserResponse(
            name=user["name"],
            email=user["email"],
            created_at=str(user["created_at"]),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(user=Depends(get_current_user)):
    """Get the current user's profile."""
    return UserResponse(
        name=user["name"],
        email=user["email"],
        created_at=str(user["created_at"]),
    )


@router.get("/stats")
async def get_stats():
    """Get public stats (user count)."""
    count = await get_user_count()
    return {"total_users": count}
