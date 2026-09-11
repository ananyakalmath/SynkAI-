"""
Summary Agent for SynkAI Sprint 4.
Extracts executive summary and meeting overview from normalized transcripts.
"""

import json
from typing import Dict, Any, Optional
from backend.agents.errors import AgentExecutionError
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "summary_agent"


class SummaryAgent:
    """
    Agent responsible for generating structured summaries from cleaned meeting transcripts.
    """

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()

    def process(self, parsed_transcript: str) -> Dict[str, Any]:
        """
        Generates executive summary and meeting overview from parsed transcript.

        Args:
            parsed_transcript (str): Cleaned/normalized transcript text.

        Returns:
            Dict[str, Any]: JSON dict containing 'executive_summary' and 'meeting_overview'.

        Raises:
            AgentExecutionError: If the LLM call or JSON parsing fails.
        """
        logger.info("Summary Agent started.")
        if not parsed_transcript or not parsed_transcript.strip():
            raise AgentExecutionError(AGENT_NAME, "Received an empty transcript.")

        system_prompt = (
            "You are a meeting summary assistant. Analyze the transcript and generate:\n"
            "1. A high-level executive summary (2-4 sentences, max 70 words).\n"
            "2. A meeting overview discussing main topics (max 80 words).\n"
            "Be concise. Do not repeat the transcript.\n\n"
            "You MUST respond ONLY with a JSON object matching this structure:\n"
            "{\n"
            "  \"executive_summary\": \"...\",\n"
            "  \"meeting_overview\": \"...\"\n"
            "}"
        )

        try:
            raw_response = self.ollama.generate(
                prompt=parsed_transcript,
                system_prompt=system_prompt,
                json_format=True,
                label=AGENT_NAME
            )
        except Exception as exc:
            logger.error(f"Summary Agent LLM call failed: {exc}")
            raise AgentExecutionError(AGENT_NAME, str(exc)) from exc

        try:
            data = json.loads(raw_response.strip())
        except (json.JSONDecodeError, AttributeError) as exc:
            logger.error(f"Summary Agent could not parse LLM JSON output: {exc}")
            raise AgentExecutionError(
                AGENT_NAME,
                f"LLM returned output that is not valid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise AgentExecutionError(AGENT_NAME, "LLM returned JSON that is not an object.")

        logger.info("Summary Agent completed successfully.")
        return {
            "executive_summary": data.get("executive_summary", ""),
            "meeting_overview": data.get("meeting_overview", "")
        }
