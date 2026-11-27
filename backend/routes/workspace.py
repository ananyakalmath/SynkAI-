"""
Workspace membership routes for SynkAI.

Lets a workspace admin see who's active and who's requesting to join, and approve or
reject those requests. Regular members can see the roster but not act on it.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config import settings
from backend.dependencies import get_session_user
from backend.models.auth import (
    InviteCreateRequest,
    InviteListResponse,
    InviteResponse,
    WorkspaceInfo,
    WorkspaceMemberOut,
    WorkspaceMembersResponse,
    WorkspaceRenameRequest,
)
from backend.services import auth_service
from backend.services.auth_service import AuthContext, AuthError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workspace", tags=["Workspace"])


def _require_workspace(context: AuthContext) -> str:
    if not context.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding before viewing a workspace.",
        )
    return context.workspace_id


def _require_admin(context: AuthContext) -> str:
    workspace_id = _require_workspace(context)
    if context.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return workspace_id


@router.get("/members", response_model=WorkspaceMembersResponse)
async def list_members(context: AuthContext = Depends(get_session_user)) -> WorkspaceMembersResponse:
    """Lists active members; pending join requests are only shown to admins."""
    workspace_id = _require_workspace(context)
    workspace = auth_service.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")

    active, pending = auth_service.list_members(workspace_id)

    return WorkspaceMembersResponse(
        workspace=WorkspaceInfo(id=workspace["id"], company_name=workspace["company_name"], domain=workspace["domain"]),
        members=[WorkspaceMemberOut(**m) for m in active],
        pending=[WorkspaceMemberOut(**m) for m in pending] if context.role == "admin" else [],
    )


@router.put("/", response_model=WorkspaceInfo)
async def rename_workspace(
    request: WorkspaceRenameRequest,
    context: AuthContext = Depends(get_session_user),
) -> WorkspaceInfo:
    """Admin-only: renames the workspace's display name (its join-matching domain never changes)."""
    workspace_id = _require_admin(context)
    auth_service.rename_workspace(workspace_id, request.company_name)
    workspace = auth_service.get_workspace(workspace_id)
    return WorkspaceInfo(id=workspace["id"], company_name=workspace["company_name"], domain=workspace["domain"])


@router.post("/invites", response_model=InviteResponse)
async def create_invite(
    request: InviteCreateRequest,
    context: AuthContext = Depends(get_session_user),
) -> InviteResponse:
    """
    Admin-only: invites someone by email to join this workspace. Works regardless of
    the invitee's email domain — this is the only way to add someone whose domain is
    public (gmail.com etc.) or simply isn't the workspace's own domain.
    """
    workspace_id = _require_admin(context)
    try:
        result = auth_service.create_invite(workspace_id, request.email, context.user_id)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return InviteResponse(**result)


@router.get("/invites", response_model=InviteListResponse)
async def list_invites(context: AuthContext = Depends(get_session_user)) -> InviteListResponse:
    """Admin-only: lists outstanding (unused, unexpired) invites for this workspace."""
    workspace_id = _require_admin(context)
    invites = auth_service.list_invites(workspace_id)
    return InviteListResponse(
        invites=[
            InviteResponse(
                code=i["code"],
                invited_email=i["invited_email"],
                expires_at=i["expires_at"],
                invite_url=f"{settings.FRONTEND_URL}?invite={i['code']}",
            )
            for i in invites
        ]
    )


@router.post("/requests/{user_id}/approve")
async def approve_request(user_id: str, context: AuthContext = Depends(get_session_user)) -> dict:
    """Admin-only: approves a pending join request."""
    workspace_id = _require_admin(context)
    try:
        auth_service.approve_membership(workspace_id, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"message": "Membership approved."}


@router.post("/requests/{user_id}/reject")
async def reject_request(user_id: str, context: AuthContext = Depends(get_session_user)) -> dict:
    """Admin-only: rejects (deletes) a pending join request."""
    workspace_id = _require_admin(context)
    try:
        auth_service.reject_membership(workspace_id, user_id)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"message": "Membership rejected."}
