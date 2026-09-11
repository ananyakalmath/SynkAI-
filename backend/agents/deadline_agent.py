"""
Deadline Agent for SynkAI Sprint 4.
Extracts deadlines, dates, milestones, and responsible persons.
"""

from typing import List, Dict, Any, Optional
from backend.agents.llm_extraction import run_json_list_extraction
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "deadline_agent"

SYSTEM_PROMPT = (
    "You are a meeting assistant. Identify all explicit deadlines, dates, and milestones discussed in the transcript. "
    "For each, extract:\n"
    "- deadline (the specific deadline statement or timeframe)\n"
    "- date (the raw date string, e.g. 'Oct 20', 'Friday')\n"
    "- milestone (the deliverable associated with the deadline)\n"
    "- responsible_person (the person responsible for the deadline, or null if not mentioned)\n\n"
    "Do not invent deadlines or assign arbitrary people. "
    "Return at most 10 deadlines and keep every field under 20 words. "
    "You MUST respond ONLY with a JSON object matching this structure:\n"
    "{\n"
    "  \"deadlines\": [\n"
    "    {\n"
    "      \"deadline\": \"...\",\n"
    "      \"date\": \"...\",\n"
    "      \"milestone\": \"...\",\n"
    "      \"responsible_person\": \"...\" or null\n"
    "    }\n"
    "  ]\n"
    "}"
)


class DeadlineAgent:
    """
    Agent responsible for extracting deadlines and milestones.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def process(self, parsed_transcript: str) -> List[Dict[str, Any]]:
        """
        Extracts deadlines from parsed transcript.

        Args:
            parsed_transcript (str): Cleaned/normalized transcript text.

        Returns:
            List[Dict[str, Any]]: List of dictionary deadline items.

        Raises:
            AgentExecutionError: If the LLM call or JSON parsing fails.
        """
        logger.info("Deadline Agent started.")
        return run_json_list_extraction(
            ollama=self.ollama,
            agent_name=AGENT_NAME,
            system_prompt=SYSTEM_PROMPT,
            parsed_transcript=parsed_transcript,
            result_key="deadlines"
        )
