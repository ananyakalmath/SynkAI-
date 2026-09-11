"""
Pydantic models for Sprint 4 Multi-Agent Meeting Intelligence.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MeetingAnalysisRequest(BaseModel):
    """
    Request model for POST /meeting/analyze.
    """
    document_id: Optional[str] = Field(default=None, description="Unique identifier of an already uploaded/indexed meeting transcript")
    transcript_text: Optional[str] = Field(default=None, description="Raw transcript text to analyze directly")


class ActionItem(BaseModel):
    """
    Structured model for extracted action items.
    """
    task: str = Field(..., description="The task description")
    owner: str = Field(..., description="The person responsible for the task")
    status: Optional[str] = Field(default=None, description="Status of the task (e.g., Pending, In Progress)")
    priority: Optional[str] = Field(default=None, description="Priority of the task (e.g., High, Medium, Low)")
    due_date: Optional[str] = Field(default=None, description="Due date or timeline if explicitly mentioned")


class Deadline(BaseModel):
    """
    Structured model for meeting deadlines and milestones.
    """
    deadline: str = Field(..., description="The deadline or time indicator")
    date: str = Field(..., description="The parsed or raw date")
    milestone: str = Field(..., description="The associated milestone or deliverable")
    responsible_person: Optional[str] = Field(default=None, description="The owner responsible for meeting the deadline")


class Risk(BaseModel):
    """
    Structured model for identified meeting risks and blockers.
    """
    risk: str = Field(..., description="Description of the risk or blocker")
    blocker: Optional[str] = Field(default=None, description="Specific blocking factor if identified")
    dependency: Optional[str] = Field(default=None, description="Dependencies associated with the risk")
    unresolved_issue: Optional[str] = Field(default=None, description="Any open or unresolved question/issue")


class AgentError(BaseModel):
    """
    Explicit record of an agent that failed during the workflow.
    Present so a failed agent is never reported as an agent that found nothing.
    """
    agent: str = Field(..., description="Name of the agent that failed")
    error: str = Field(..., description="Reason the agent could not complete")


class MeetingAnalysisResponse(BaseModel):
    """
    Unified multi-agent response containing all meeting intelligence components.
    """
    executive_summary: str = Field(..., description="Concise executive summary of the meeting")
    meeting_overview: Optional[str] = Field(default=None, description="Detailed overview of the meeting topics")
    action_items: List[ActionItem] = Field(default_factory=list, description="List of extracted action items")
    decisions: List[str] = Field(default_factory=list, description="List of decisions made, agreements, and approvals")
    deadlines: List[Deadline] = Field(default_factory=list, description="List of dates, deadlines, and milestones")
    risks: List[Risk] = Field(default_factory=list, description="List of risks, blockers, dependencies, and unresolved issues")
    analysis_complete: bool = Field(default=True, description="False when one or more agents failed to produce output")
    agent_errors: List[AgentError] = Field(default_factory=list, description="Agents that failed, with the reason for each")
