"""
Authentication, onboarding, and profile routes for SynkAI.

No passwords: accounts exist only via "Sign in with Google" or an emailed one-time
code. A brand-new account must complete onboarding (name, company, role) before it
can do anything else — see backend.dependencies.get_current_user.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_session_token_and_user, get_session_user
from backend.models.auth import (
    AuthResult,
    EmailCodeRequest,
    EmailCodeVerifyRequest,
    GoogleCallbackRequest,
    GoogleLoginURLResponse,
    OnboardingRequest,
    ProfileUpdateRequest,
    UserProfileResponse,
    WorkspaceInfo,
)
from backend.services import auth_service, google_oauth_service
from backend.services.auth_service import AuthContext, AuthError, RateLimitError
from backend.services.google_oauth_service import GoogleOAuthError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _profile_for(context: AuthContext) -> UserProfileResponse:
    workspace = None
    if context.workspace_id:
        ws = auth_service.get_workspace(context.workspace_id)
        if ws:
            workspace = WorkspaceInfo(id=ws["id"], company_name=ws["company_name"], domain=ws["domain"])

    return UserProfileResponse(
        id=context.user_id,
        email=context.email,
        full_name=context.full_name,
        onboarded=context.onboarded,
        google_connected=context.google_connected,
        role_title=context.title,
        workspace=workspace,
        membership_role=context.role,
        membership_status=context.membership_status,
    )


@router.get("/google/login", response_model=GoogleLoginURLResponse)
async def google_login(invite_code: Optional[str] = None) -> GoogleLoginURLResponse:
    """
    Returns the URL to send the user to for Google sign-in. `invite_code`, if the user
    arrived via an invite link, rides through the redirect inside the state record and
    comes back in the callback response.
    """
    state = auth_service.create_oauth_state(invite_code)
    try:
        url = google_oauth_service.build_authorization_url(state)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return GoogleLoginURLResponse(authorization_url=url, state=state)


@router.post("/google/callback", response_model=AuthResult)
async def google_callback(request: GoogleCallbackRequest) -> AuthResult:
    """Exchanges a Google authorization code for a SynkAI session."""
    state_record = auth_service.consume_oauth_state(request.state)
    if state_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-in link has expired or was already used. Please try again.",
        )

    try:
        tokens = google_oauth_service.exchange_code_for_tokens(request.code)
        userinfo = google_oauth_service.fetch_userinfo(tokens["access_token"])
    except GoogleOAuthError as exc:
        logger.error(f"Google sign-in failed: {exc}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google did not return the expected profile information.",
        )

    user_id = auth_service.get_or_create_user_by_google(sub, email, userinfo.get("name"))
    session_token = auth_service.create_session(user_id)
    context = auth_service.resolve_session(session_token)

    return AuthResult(
        session_token=session_token,
        user=_profile_for(context),
        invite_code=state_record.get("invite_code"),
    )


@router.post("/email/request-code")
async def request_email_code(request: EmailCodeRequest) -> dict:
    """Emails a one-time, 10-minute, single-use login code to the given address."""
    try:
        auth_service.request_email_code(request.email)
    except RateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"message": "If that email is valid, a sign-in code has been sent."}


@router.post("/email/verify-code", response_model=AuthResult)
async def verify_email_code(request: EmailCodeVerifyRequest) -> AuthResult:
    """Verifies a login code and issues a session."""
    try:
        valid = auth_service.verify_email_code(request.email, request.code)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired code.")

    user_id = auth_service.get_or_create_user_by_email(request.email)
    session_token = auth_service.create_session(user_id)
    context = auth_service.resolve_session(session_token)

    return AuthResult(session_token=session_token, user=_profile_for(context))


@router.get("/me", response_model=UserProfileResponse)
async def get_me(context: AuthContext = Depends(get_session_user)) -> UserProfileResponse:
    """Returns the current session's user, onboarding state, and workspace/role."""
    return _profile_for(context)


@router.post("/onboarding", response_model=UserProfileResponse)
async def onboarding(
    request: OnboardingRequest,
    context: AuthContext = Depends(get_session_user),
) -> UserProfileResponse:
    """
    Completes a new account's profile and places them in a workspace — via an invite
    code, or else matched by the user's verified email domain (never by a public/
    freemail domain, and never by the company name they typed).
    """
    try:
        auth_service.complete_onboarding(
            context.user_id,
            request.full_name,
            request.company_name,
            request.role_title,
            invite_code=request.invite_code,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    refreshed = auth_service.get_context(context.user_id)
    return _profile_for(refreshed)


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    context: AuthContext = Depends(get_session_user),
) -> UserProfileResponse:
    """Updates the editable parts of a profile: full name and role/title."""
    auth_service.update_profile(context.user_id, request.full_name, request.role_title)
    return _profile_for(auth_service.get_context(context.user_id))


@router.post("/logout")
async def logout(token_and_context=Depends(get_session_token_and_user)) -> dict:
    """Logs out the current session only."""
    token, _ = token_and_context
    auth_service.revoke_session(token)
    return {"message": "Logged out."}


@router.post("/logout-all")
async def logout_all(context: AuthContext = Depends(get_session_user)) -> dict:
    """Logs out every session/device for this user."""
    auth_service.revoke_all_sessions(context.user_id)
    return {"message": "Logged out of all devices."}
