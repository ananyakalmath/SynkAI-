"""
Pydantic schemas for accounts, sessions, onboarding, and workspace membership.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class GoogleLoginURLResponse(BaseModel):
    authorization_url: str = Field(..., description="Google OAuth consent screen URL to redirect the user to")
    state: str = Field(..., description="CSRF state token embedded in the authorization URL")


class GoogleCallbackRequest(BaseModel):
    code: str = Field(..., description="Authorization code returned by Google")
    state: str = Field(..., description="State token returned by Google, verified against the one we issued")


class EmailCodeRequest(BaseModel):
    email: EmailStr = Field(..., description="Work email address to send a one-time login code to")


class EmailCodeVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=12)


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    role_title: str = Field(..., min_length=1)


class WorkspaceRenameRequest(BaseModel):
    company_name: str = Field(..., min_length=1)


class OnboardingRequest(BaseModel):
    full_name: str = Field(..., min_length=1, description="The user's full name")
    role_title: str = Field(..., min_length=1, description="Role or title, e.g. CEO, Manager")
    company_name: Optional[str] = Field(
        default=None,
        description="Display name for a new workspace. Not needed when joining via invite_code.",
    )
    invite_code: Optional[str] = Field(
        default=None,
        description="A workspace invite code — joins that exact workspace, bypassing domain matching.",
    )


class WorkspaceInfo(BaseModel):
    id: str
    company_name: str
    domain: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    onboarded: bool
    google_connected: bool = False
    role_title: Optional[str] = None
    workspace: Optional[WorkspaceInfo] = None
    membership_role: Optional[str] = Field(default=None, description="'admin' or 'member' within the workspace")
    membership_status: Optional[str] = Field(default=None, description="'active' or 'pending'")


class AuthResult(BaseModel):
    session_token: str
    user: UserProfileResponse
    invite_code: Optional[str] = Field(
        default=None,
        description="Carried through from a Google sign-in started via an invite link",
    )


class WorkspaceMemberOut(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    email: str
    role: str
    status: str
    title: Optional[str] = None


class WorkspaceMembersResponse(BaseModel):
    workspace: WorkspaceInfo
    members: List[WorkspaceMemberOut]
    pending: List[WorkspaceMemberOut]


class InviteCreateRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to invite to the workspace")


class InviteResponse(BaseModel):
    code: str
    invited_email: str
    expires_at: str
    invite_url: str
    email_sent: bool = True
    email_error: Optional[str] = None


class InviteListResponse(BaseModel):
    invites: List[InviteResponse]
