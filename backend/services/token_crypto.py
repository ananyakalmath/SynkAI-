"""
Encrypts/decrypts Google refresh tokens before they touch the database (Phase 3).

A refresh token is a long-lived credential — if the database were ever read by
someone who shouldn't, a plaintext refresh token would let them act as that user's
Google Calendar indefinitely. Fernet (symmetric, authenticated) keeps this simple:
one key from `.env`, no key management service needed for a local-first app.
"""

from cryptography.fernet import Fernet, InvalidToken

from backend.config import settings


class TokenEncryptionError(Exception):
    """Raised when TOKEN_ENCRYPTION_KEY is missing/invalid, or a stored token won't decrypt."""


def _fernet() -> Fernet:
    if not settings.TOKEN_ENCRYPTION_KEY:
        raise TokenEncryptionError(
            "TOKEN_ENCRYPTION_KEY is not configured — Google Calendar connections cannot be stored."
        )
    try:
        return Fernet(settings.TOKEN_ENCRYPTION_KEY.encode("utf-8"))
    except Exception as exc:
        raise TokenEncryptionError(f"TOKEN_ENCRYPTION_KEY is not a valid Fernet key: {exc}") from exc


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise TokenEncryptionError("Stored Google token could not be decrypted (key changed?).") from exc
