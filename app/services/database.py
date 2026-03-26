"""
database.py – MongoDB connection and user CRUD operations.

Uses Motor (async MongoDB driver) for non-blocking database access.
Passwords are hashed with bcrypt before storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import bcrypt

from app.utils.helpers import get_env, setup_logging

logger = setup_logging("drcode.database")

# ──────────────────────────────────────────────
#  MongoDB connection (lazy singleton)
# ──────────────────────────────────────────────
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get or create the MongoDB connection."""
    global _client, _db
    if _db is None:
        uri = get_env("MONGODB_URI", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(uri)
        _db = _client["drcode"]
        logger.info("Connected to MongoDB at %s", uri)
    return _db


async def close_database() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


# ──────────────────────────────────────────────
#  Password hashing
# ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ──────────────────────────────────────────────
#  User CRUD
# ──────────────────────────────────────────────

async def create_user(name: str, email: str, password: str) -> Dict[str, Any]:
    """
    Create a new user in the database.

    Returns the created user document (without password).
    Raises ValueError if email already exists.
    """
    db = await get_database()
    collection = db["users"]

    # Check if user already exists
    existing = await collection.find_one({"email": email.lower()})
    if existing:
        raise ValueError("A user with this email already exists.")

    user_doc = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hash_password(password),
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
        "login_count": 1,
    }

    result = await collection.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    del user_doc["password"]
    logger.info("User created: %s", email)
    return user_doc


async def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by email. Returns None if not found."""
    db = await get_database()
    collection = db["users"]
    user = await collection.find_one({"email": email.lower().strip()})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def update_login(email: str) -> None:
    """Update user's last login timestamp and increment login count."""
    db = await get_database()
    collection = db["users"]
    await collection.update_one(
        {"email": email.lower()},
        {
            "$set": {"last_login": datetime.now(timezone.utc)},
            "$inc": {"login_count": 1},
        },
    )


async def get_user_count() -> int:
    """Get total number of registered users."""
    db = await get_database()
    return await db["users"].count_documents({})
