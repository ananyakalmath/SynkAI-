"""
Google OAuth 2.0 / OpenID Connect Service for SynkAI.

Plain REST calls via `requests` rather than the google-auth SDKs — the same "direct
HTTP client" choice made for Ollama (see ollama_service.py): fewer dependencies, and
the handful of endpoints involved (authorize, token, userinfo) are simple, stable,
and easy to mock in tests.

Phase 1 only requests `openid email profile` (sign-in). The `calendar.events` scope
used in Phase 3 is requested later, incrementally, when a user explicitly connects
Google Calendar — not bundled into every login.
"""

from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"

LOGIN_SCOPES = "openid email profile"

# Requested only when a user explicitly clicks "Connect Google Calendar" (Phase 3's
# incremental authorization) — never bundled into ordinary sign-in.
CALENDAR_SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"


class GoogleOAuthError(Exception):
    """Raised when any step of the Google OAuth exchange fails."""


def build_authorization_url(state: str, scopes: str = LOGIN_SCOPES, extra_params: Optional[Dict[str, str]] = None) -> str:
    """Builds the URL the user is sent to on Google's consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleOAuthError("GOOGLE_CLIENT_ID is not configured.")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "prompt": "select_account",
    }
    params.update(extra_params or {})
    return f"{AUTH_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchanges an authorization code for access/id/refresh tokens."""
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(TOKEN_ENDPOINT, data=payload, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise GoogleOAuthError(f"Could not reach Google's token endpoint: {exc}") from exc

    if response.status_code != 200:
        raise GoogleOAuthError(f"Google token exchange failed (HTTP {response.status_code}): {response.text}")

    return response.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Exchanges a stored refresh token for a new short-lived access token."""
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        response = requests.post(TOKEN_ENDPOINT, data=payload, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise GoogleOAuthError(f"Could not reach Google's token endpoint: {exc}") from exc

    if response.status_code != 200:
        raise GoogleOAuthError(f"Google token refresh failed (HTTP {response.status_code}): {response.text}")

    return response.json()


def fetch_userinfo(access_token: str) -> Dict[str, Any]:
    """Fetches the signed-in user's profile (sub, email, name, ...)."""
    try:
        response = requests.get(
            USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise GoogleOAuthError(f"Could not reach Google's userinfo endpoint: {exc}") from exc

    if response.status_code != 200:
        raise GoogleOAuthError(f"Google userinfo request failed (HTTP {response.status_code}): {response.text}")

    return response.json()
