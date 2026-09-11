"""
Action Item Agent for SynkAI Sprint 4.
Extracts tasks, owners, statuses, priorities, and due dates from transcript.
"""

from typing import List, Dict, Any, Optional
from backend.agents.llm_extraction import run_json_list_extraction
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "action_item_agent"

SYSTEM_PROMPT = (
    "You are a meeting analysis assistant. Identify all action items, tasks, and assignments in the transcript. "
    "For each action item, extract:\n"
    "- task (description)\n"
    "- owner (person responsible)\n"
    "- status (e.g. Pending, Completed, or null if not mentioned)\n"
    "- priority (e.g. High, Medium, Low, or null if not mentioned)\n"
    "- due_date (deadline or due day if explicitly mentioned, or null)\n\n"
    "Do not invent owners or tasks. Only extract items directly mentioned. "
    "Return at most 10 action items and keep every field under 20 words. "
    "You MUST respond ONLY with a JSON object matching this structure:\n"
    "{\n"
    "  \"action_items\": [\n"
    "    {\n"
    "      \"task\": \"...\",\n"
    "      \"owner\": \"...\",\n"
    "      \"status\": \"...\" or null,\n"
    "      \"priority\": \"...\" or null,\n"
    "      \"due_date\": \"...\" or null\n"
    "    }\n"
    "  ]\n"
    "}"
)


class ActionItemAgent:
    """
    Agent responsible for extracting action items, assignments, and due dates.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def process(self, parsed_transcript: str) -> List[Dict[str, Any]]:
        """
        Extracts action items from parsed transcript.

        Args:
            parsed_transcript (str): Cleaned/normalized transcript text.

        Returns:
            List[Dict[str, Any]]: List of dictionary action items.

        Raises:
            AgentExecutionError: If the LLM call or JSON parsing fails.
        """
        logger.info("Action Item Agent started.")
        return run_json_list_extraction(
            ollama=self.ollama,
            agent_name=AGENT_NAME,
            system_prompt=SYSTEM_PROMPT,
            parsed_transcript=parsed_transcript,
            result_key="action_items"
        )
