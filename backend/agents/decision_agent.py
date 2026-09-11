"""
Decision Agent for SynkAI Sprint 4.
Extracts decisions, agreements, approvals, and key choices from meeting transcript.
"""

from typing import List, Optional
from backend.agents.llm_extraction import run_json_list_extraction
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "decision_agent"

SYSTEM_PROMPT = (
    "You are a meeting intelligence assistant. Identify all major decisions, agreements reached, "
    "approvals given, or key choices made in the meeting transcript. Do not include tasks or risks. "
    "Do not invent information. Return at most 10 decisions, each under 25 words. "
    "You MUST respond ONLY with a JSON object matching this structure:\n"
    "{\n"
    "  \"decisions\": [\n"
    "    \"Decision text 1\",\n"
    "    \"Decision text 2\"\n"
    "  ]\n"
    "}"
)


class DecisionAgent:
    """
    Agent responsible for extracting decisions made during the meeting.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def process(self, parsed_transcript: str) -> List[str]:
        """
        Extracts decisions from parsed transcript.

        Args:
            parsed_transcript (str): Cleaned/normalized transcript text.

        Returns:
            List[str]: List of extracted decision description strings.

        Raises:
            AgentExecutionError: If the LLM call or JSON parsing fails.
        """
        logger.info("Decision Agent started.")
        return run_json_list_extraction(
            ollama=self.ollama,
            agent_name=AGENT_NAME,
            system_prompt=SYSTEM_PROMPT,
            parsed_transcript=parsed_transcript,
            result_key="decisions"
        )
