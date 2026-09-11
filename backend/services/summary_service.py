"""
Summary Service for SynkAI.
Orchestrates AI-powered meeting transcript summarization via Ollama.
"""

import json
import re
from typing import Dict, Any
from backend.services.ollama_service import OllamaService
from backend.models.summary import SummaryResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = """You are SynkAI, an expert executive meeting assistant.
Your task is to analyze the provided meeting transcript and produce a highly structured, accurate summary.

You MUST respond ONLY with a valid JSON object matching the following structure:
{
  "executive_summary": "A concise 2-4 sentence overview of the meeting's core objective and main discussion.",
  "key_discussion_points": [
    "Discussion point 1 with relevant detail",
    "Discussion point 2 with relevant detail",
    "Discussion point 3 with relevant detail"
  ],
  "meeting_outcome": "Clear summary of decisions reached, next steps, and final outcomes."
}

Do not include any intro, markdown preambles, or conversational commentary outside the JSON object.
"""


class SummaryService:
    """
    Service generating structured meeting summaries using Ollama LLM.
    """

    def __init__(self, ollama_service: OllamaService = None):
        self.ollama = ollama_service or OllamaService()

    def generate_summary(self, transcript_text: str, filename: str = None) -> SummaryResponse:
        """
        Processes a meeting transcript and returns a structured SummaryResponse.

        Args:
            transcript_text (str): Raw text of the meeting transcript.
            filename (str, optional): Name of the source file.

        Returns:
            SummaryResponse: Structured summary object.
        """
        if not transcript_text or not transcript_text.strip():
            logger.error("Empty transcript text provided for summarization.")
            raise ValueError("Transcript text cannot be empty.")

        logger.info(
            f"Summarizing transcript ({len(transcript_text)} characters) using Ollama model '{self.ollama.model}'..."
        )

        prompt = (
            f"Meeting Transcript:\n---\n{transcript_text}\n---\n"
            "Provide the structured JSON summary."
        )

        raw_output = self.ollama.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_format=True,
            label="summary_service",
        )

        parsed_data = self._parse_llm_json(raw_output)

        return SummaryResponse(
            executive_summary=parsed_data.get(
                "executive_summary",
                "No executive summary could be generated.",
            ),
            key_discussion_points=parsed_data.get(
                "key_discussion_points",
                ["No key discussion points identified."],
            ),
            meeting_outcome=parsed_data.get(
                "meeting_outcome",
                "No clear meeting outcomes recorded.",
            ),
            model_used=self.ollama.model,
            filename=filename,
        )

    @staticmethod
    def _parse_llm_json(raw_output: str) -> Dict[str, Any]:
        """
        Safely parses JSON output from LLM, handling potential markdown code fences.
        """
        if not raw_output:
            return {}

        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\n?",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(r"\n?```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)

            if isinstance(data, dict):
                points = data.get("key_discussion_points", [])

                if isinstance(points, str):
                    data["key_discussion_points"] = [points]

                return data

        except json.JSONDecodeError as exc:
            logger.warning(
                f"Failed to parse direct JSON from LLM output: {exc}. Extracting fallback content..."
            )

        return {
            "executive_summary": raw_output[:300] + "...",
            "key_discussion_points": [
                line.strip("- *")
                for line in raw_output.split("\n")
                if line.strip().startswith(("-", "*", "1.", "2."))
            ][:5],
            "meeting_outcome": "Extracted summary outcome from response.",
        }