"""
Shared FastAPI dependencies for authentication and workspace scoping.

`get_current_user` is the single gate every route that touches meetings, documents,
tasks, or RAG data depends on — so "does this request belong to this workspace" is
answered in exactly one place, not re-implemented per route.
"""

from typing import Optional, Tuple

from fastapi import Header, HTTPException, status

from backend.services.auth_service import AuthContext, AuthError, resolve_session


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return authorization.split(" ", 1)[1].strip()


async def get_session_token_and_user(
    authorization: Optional[str] = Header(default=None),
) -> Tuple[str, AuthContext]:
    """
    Resolves the raw token alongside the caller's context — logout needs the raw
    token itself (to revoke that one session) as well as the validated identity.
    """
    token = _extract_token(authorization)
    try:
        return token, resolve_session(token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def get_session_user(authorization: Optional[str] = Header(default=None)) -> AuthContext:
    """
    Resolves the caller's session without requiring onboarding or an active workspace.
    Used by the auth/onboarding/workspace endpoints themselves, which a brand-new or
    still-pending user must be able to call.
    """
    _, context = await get_session_token_and_user(authorization)
    return context


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> AuthContext:
    """
    Resolves the caller and requires a completed profile and an active workspace
    membership. Depend on this (not get_session_user) from any route that reads or
    writes meeting, document, task, or RAG data.
    """
    context = await get_session_user(authorization)

    if not context.onboarded or context.workspace_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete onboarding before using SynkAI.",
        )

    if context.membership_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your workspace membership is pending approval from an admin.",
        )

    return context
