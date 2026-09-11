"""
Risk Agent for SynkAI Sprint 4.
Identifies risks, blockers, dependencies, and unresolved issues from transcript.
"""

from typing import List, Dict, Any, Optional
from backend.agents.llm_extraction import run_json_list_extraction
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "risk_agent"

SYSTEM_PROMPT = (
    "You are a risk analysis assistant. Identify all blockers, dependencies, risks, and unresolved issues "
    "discussed in the meeting transcript. For each issue, extract:\n"
    "- risk (description of the risk/blocker)\n"
    "- blocker (what is specifically blocking progress, or null)\n"
    "- dependency (dependencies on other teams/tasks, or null)\n"
    "- unresolved_issue (details about any open questions or undecided items, or null)\n\n"
    "Do not invent information or extrapolate. Only extract items directly mentioned. "
    "Return at most 10 risks and keep every field under 20 words. "
    "You MUST respond ONLY with a JSON object matching this structure:\n"
    "{\n"
    "  \"risks\": [\n"
    "    {\n"
    "      \"risk\": \"...\",\n"
    "      \"blocker\": \"...\" or null,\n"
    "      \"dependency\": \"...\" or null,\n"
    "      \"unresolved_issue\": \"...\" or null\n"
    "    }\n"
    "  ]\n"
    "}"
)


class RiskAgent:
    """
    Agent responsible for identifying and structuring risks and blockers.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def process(self, parsed_transcript: str) -> List[Dict[str, Any]]:
        """
        Extracts risks and blockers from parsed transcript.

        Args:
            parsed_transcript (str): Cleaned/normalized transcript text.

        Returns:
            List[Dict[str, Any]]: List of dictionary risk items.

        Raises:
            AgentExecutionError: If the LLM call or JSON parsing fails.
        """
        logger.info("Risk Agent started.")
        return run_json_list_extraction(
            ollama=self.ollama,
            agent_name=AGENT_NAME,
            system_prompt=SYSTEM_PROMPT,
            parsed_transcript=parsed_transcript,
            result_key="risks"
        )
