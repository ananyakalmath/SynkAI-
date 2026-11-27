"""
Google Calendar connect/disconnect routes (Phase 3).

Incremental authorization: the calendar.events scope is only ever requested when a
signed-in user explicitly clicks "Connect Google Calendar" here — never bundled into
ordinary sign-in (see google_oauth_service.LOGIN_SCOPES vs CALENDAR_SCOPES).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_current_user
from backend.models.google_calendar import (
    GoogleCalendarCallbackRequest,
    GoogleCalendarConnectResponse,
    GoogleCalendarStatusResponse,
)
from backend.services import auth_service, google_calendar_service, google_oauth_service
from backend.services.auth_service import AuthContext
from backend.services.google_oauth_service import CALENDAR_SCOPES, GoogleOAuthError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth/google/calendar", tags=["Google Calendar"])


@router.get("/connect", response_model=GoogleCalendarConnectResponse)
async def connect(current: AuthContext = Depends(get_current_user)) -> GoogleCalendarConnectResponse:
    """Returns the URL to send the user to for incremental calendar authorization."""
    state = auth_service.create_calendar_connect_state(current.user_id)
    try:
        url = google_oauth_service.build_authorization_url(
            state,
            scopes=CALENDAR_SCOPES,
            # access_type=offline to get a refresh token; prompt=consent to guarantee
            # one is issued even if this user granted access once before.
            extra_params={"access_type": "offline", "prompt": "consent"},
        )
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return GoogleCalendarConnectResponse(authorization_url=url, state=state)


@router.post("/connect/callback", response_model=GoogleCalendarStatusResponse)
async def connect_callback(request: GoogleCalendarCallbackRequest) -> GoogleCalendarStatusResponse:
    """Exchanges the authorization code and stores the resulting refresh token, encrypted."""
    state_record = auth_service.consume_oauth_state(request.state)
    if (
        state_record is None
        or state_record.get("purpose") != "calendar_connect"
        or not state_record.get("user_id")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Google Calendar connection link has expired or was already used. Please try again.",
        )

    try:
        tokens = google_oauth_service.exchange_code_for_tokens(request.code)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Google didn't grant a long-lived connection. If you've connected this app before, "
                "remove its access under your Google Account's third-party permissions and try again."
            ),
        )

    google_calendar_service.save_connection(
        user_id=state_record["user_id"],
        refresh_token=refresh_token,
        access_token=tokens.get("access_token"),
        expires_in=tokens.get("expires_in"),
        scope=tokens.get("scope"),
    )
    return GoogleCalendarStatusResponse(connected=True)


@router.post("/disconnect", response_model=GoogleCalendarStatusResponse)
async def disconnect(current: AuthContext = Depends(get_current_user)) -> GoogleCalendarStatusResponse:
    google_calendar_service.disconnect(current.user_id)
    return GoogleCalendarStatusResponse(connected=False)


@router.get("/status", response_model=GoogleCalendarStatusResponse)
async def connection_status(current: AuthContext = Depends(get_current_user)) -> GoogleCalendarStatusResponse:
    return GoogleCalendarStatusResponse(connected=google_calendar_service.is_connected(current.user_id))
