"""
Coordinator Agent for SynkAI Sprint 4.
Collects and aggregates outputs from all specialized agents into a unified, structured response.
"""

from typing import Dict, Any, List, Optional
from backend.models.analysis import MeetingAnalysisResponse, ActionItem, AgentError, Deadline, Risk
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CoordinatorAgent:
    """
    Agent responsible for compiling final meeting intelligence outputs.
    """

    def process(
        self,
        summary_data: Dict[str, Any],
        action_items: List[Dict[str, Any]],
        decisions: List[str],
        deadlines: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        agent_errors: Optional[List[Dict[str, str]]] = None
    ) -> MeetingAnalysisResponse:
        """
        Aggregates individual agent outputs into a validated MeetingAnalysisResponse.

        Args:
            summary_data (Dict[str, Any]): Output of SummaryAgent.
            action_items (List[Dict[str, Any]]): Output of ActionItemAgent.
            decisions (List[str]): Output of DecisionAgent.
            deadlines (List[Dict[str, Any]]): Output of DeadlineAgent.
            risks (List[Dict[str, Any]]): Output of RiskAgent.
            agent_errors (Optional[List[Dict[str, str]]]): Agents that failed during the workflow.

        Returns:
            MeetingAnalysisResponse: Validated response payload.
        """
        logger.info("Coordinator Agent started.")

        # Safely convert action items to Pydantic objects
        validated_action_items = []
        for item in action_items:
            try:
                validated_action_items.append(
                    ActionItem(
                        task=item.get("task", ""),
                        owner=item.get("owner", ""),
                        status=item.get("status"),
                        priority=item.get("priority"),
                        due_date=item.get("due_date")
                    )
                )
            except Exception as exc:
                logger.warning(f"Failed to parse action item {item}: {exc}")

        # Safely convert deadlines to Pydantic objects
        validated_deadlines = []
        for dl in deadlines:
            try:
                validated_deadlines.append(
                    Deadline(
                        deadline=dl.get("deadline", ""),
                        date=dl.get("date", ""),
                        milestone=dl.get("milestone", ""),
                        responsible_person=dl.get("responsible_person")
                    )
                )
            except Exception as exc:
                logger.warning(f"Failed to parse deadline {dl}: {exc}")

        # Safely convert risks to Pydantic objects
        validated_risks = []
        for r in risks:
            try:
                validated_risks.append(
                    Risk(
                        risk=r.get("risk", ""),
                        blocker=r.get("blocker"),
                        dependency=r.get("dependency"),
                        unresolved_issue=r.get("unresolved_issue")
                    )
                )
            except Exception as exc:
                logger.warning(f"Failed to parse risk {r}: {exc}")

        # Surface agent failures explicitly instead of passing off empty results as success.
        validated_errors = [
            AgentError(agent=err.get("agent", "unknown_agent"), error=err.get("error", "Unknown error"))
            for err in (agent_errors or [])
        ]

        if validated_errors:
            failed_names = ", ".join(err.agent for err in validated_errors)
            logger.error(f"Coordinator assembling a PARTIAL analysis. Failed agents: {failed_names}.")

        response = MeetingAnalysisResponse(
            executive_summary=summary_data.get("executive_summary", ""),
            meeting_overview=summary_data.get("meeting_overview"),
            action_items=validated_action_items,
            decisions=decisions,
            deadlines=validated_deadlines,
            risks=validated_risks,
            analysis_complete=not validated_errors,
            agent_errors=validated_errors
        )

        logger.info(
            f"Coordinator Agent completed (complete={response.analysis_complete}, "
            f"action_items={len(validated_action_items)}, decisions={len(decisions)}, "
            f"deadlines={len(validated_deadlines)}, risks={len(validated_risks)})."
        )
        return response
