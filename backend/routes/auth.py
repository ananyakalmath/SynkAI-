"""
Authentication and profile routes for SynkAI.

Handles user signup, login, profile updates, and logout.
User accounts are persisted in data/users.json.
"""

import asyncio
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, EmailStr


PROJECT_ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = PROJECT_ROOT / "data" / "users.json"

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    workspace: str = "SynkAI"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str
    email: EmailStr
    workspace: str


def _load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        return {"users": {}}

    try:
        with USERS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"users": {}}

        data.setdefault("users", {})
        return data

    except (json.JSONDecodeError, OSError):
        return {"users": {}}


def _save_users(data: Dict[str, Any]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = USERS_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary_file.replace(USERS_FILE)


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()

    return f"{salt}${password_hash}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected_hash = stored_hash.split("$", 1)
    except ValueError:
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()

    return secrets.compare_digest(actual_hash, expected_hash)


def _find_user_by_email(
    users: Dict[str, Any],
    email: str,
) -> tuple[str | None, Dict[str, Any] | None]:
    target = email.strip().lower()

    for user_id, user in users.items():
        if user.get("email", "").lower() == target:
            return user_id, user

    return None, None


def _get_authenticated_user(
    auth_token: str | None,
    data: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    users = data.get("users", {})

    for user_id, user in users.items():
        if user.get("auth_token") == auth_token:
            return user_id, user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
    )


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
)
async def signup(request: SignupRequest) -> Dict[str, Any]:
    """Create a new SynkAI account."""

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    name = request.name.strip()
    workspace = request.workspace.strip() or "SynkAI"
    email = request.email.strip().lower()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required.",
        )

    data = _load_users()
    users = data["users"]

    _, existing_user = _find_user_by_email(users, email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_id = secrets.token_hex(16)
    auth_token = secrets.token_urlsafe(32)

    # Password hashing is CPU work, so run it outside the async event loop.
    password_hash = await asyncio.to_thread(
        _hash_password,
        request.password,
    )

    users[user_id] = {
        "id": user_id,
        "name": name,
        "email": email,
        "workspace": workspace,
        "role": "Workspace owner",
        "password_hash": password_hash,
        "auth_token": auth_token,
    }

    await asyncio.to_thread(_save_users, data)

    return {
        "message": "Account created successfully.",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "workspace": workspace,
            "role": "Workspace owner",
        },
        "auth_token": auth_token,
    }


@router.post("/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """Log an existing user into SynkAI."""

    data = await asyncio.to_thread(_load_users)
    users = data["users"]

    user_id, user = _find_user_by_email(
        users,
        request.email,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Password verification is CPU-intensive, so don't block
    # FastAPI's async event loop while doing it.
    password_valid = await asyncio.to_thread(
        _verify_password,
        request.password,
        user.get("password_hash", ""),
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    auth_token = secrets.token_urlsafe(32)
    user["auth_token"] = auth_token

    await asyncio.to_thread(_save_users, data)

    return {
        "message": "Login successful.",
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "workspace": user.get("workspace", "SynkAI"),
            "role": user.get("role", "Workspace owner"),
        },
        "auth_token": auth_token,
    }


@router.get("/profile")
async def get_profile(
    x_auth_token: str | None = Header(default=None),
) -> Dict[str, Any]:
    """Return the currently authenticated user's profile."""

    data = await asyncio.to_thread(_load_users)

    user_id, user = _get_authenticated_user(
        x_auth_token,
        data,
    )

    return {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "workspace": user.get("workspace", "SynkAI"),
        "role": user.get("role", "Workspace owner"),
    }


@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    x_auth_token: str | None = Header(default=None),
) -> Dict[str, Any]:
    """Update and permanently save the authenticated user's profile."""

    data = await asyncio.to_thread(_load_users)

    user_id, user = _get_authenticated_user(
        x_auth_token,
        data,
    )

    name = request.name.strip()
    workspace = request.workspace.strip() or "SynkAI"
    email = request.email.strip().lower()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required.",
        )

    existing_id, existing_user = _find_user_by_email(
        data["users"],
        email,
    )

    if existing_user and existing_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email is already being used by another account.",
        )

    user["name"] = name
    user["email"] = email
    user["workspace"] = workspace

    await asyncio.to_thread(_save_users, data)

    return {
        "message": "Profile updated successfully.",
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "workspace": user["workspace"],
            "role": user.get("role", "Workspace owner"),
        },
    }


@router.post("/logout")
async def logout(
    x_auth_token: str | None = Header(default=None),
) -> Dict[str, str]:
    """Invalidate the current authentication token."""

    data = await asyncio.to_thread(_load_users)

    _, user = _get_authenticated_user(
        x_auth_token,
        data,
    )

    user["auth_token"] = None

    await asyncio.to_thread(_save_users, data)

    return {
        "message": "Logged out successfully."
    }