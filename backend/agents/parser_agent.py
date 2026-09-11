"""
Parser Agent for SynkAI Sprint 4.
Cleans and normalizes transcript formatting, preserving speaker information and transcript details.

This agent is deliberately deterministic: transcript normalization is pure string work, so it
runs in Python instead of spending a qwen3 generation (and a slot on the local Ollama server)
on a task that needs no reasoning. It remains a first-class node in the LangGraph workflow.
"""

import re
from backend.agents.errors import AgentExecutionError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_NAME = "parser_agent"

# [00:12], (00:12:34), 00:12:34 at the start of a line - meeting tool timestamp noise.
TIMESTAMP_BRACKET_PATTERN = re.compile(r"[\[\(]\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp]\.?[Mm]\.?)?\s*[\]\)]")
TIMESTAMP_LINE_PREFIX_PATTERN = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?\s*[-–—]?\s*")

# Exporter artifacts such as "Page 3", "Page 3 of 12", "--- Page 3 ---".
PAGE_MARKER_PATTERN = re.compile(r"^[-–—\s]*page\s+\d+(\s+of\s+\d+)?[-–—\s]*$", re.IGNORECASE)

# Transcription noise markers: [inaudible], (crosstalk), [background noise].
NOISE_MARKER_PATTERN = re.compile(
    r"[\[\(]\s*(inaudible|crosstalk|cross talk|background noise|silence|laughter|music|unintelligible)[^\]\)]*[\]\)]",
    re.IGNORECASE
)

# "Speaker Name:" at the start of a line, used to normalize spacing around speaker tags.
# Restricted to name-like prefixes so URLs ("http://...") are left untouched.
SPEAKER_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9 .'\-]{0,58}?)\s*:\s*(?!/)(.*)$")

MULTI_SPACE_PATTERN = re.compile(r"[ \t ]+")


class ParserAgent:
    """
    Agent responsible for cleaning, normalising, and structuring meeting transcripts.
    """

    def process(self, transcript_text: str) -> str:
        """
        Cleans unnecessary formatting and normalizes a meeting transcript, preserving
        speaker tags and every discussion point verbatim.

        Args:
            transcript_text (str): Raw transcript content.

        Returns:
            str: Cleaned and structured transcript.

        Raises:
            AgentExecutionError: If the transcript is empty or cleaning leaves no content.
        """
        logger.info("Parser Agent started (deterministic text normalization, no LLM call).")

        if not transcript_text or not transcript_text.strip():
            raise AgentExecutionError(AGENT_NAME, "Received an empty transcript.")

        cleaned_lines = []

        for raw_line in transcript_text.splitlines():
            line = raw_line.replace(" ", " ")
            line = TIMESTAMP_BRACKET_PATTERN.sub(" ", line)
            line = NOISE_MARKER_PATTERN.sub(" ", line)
            line = TIMESTAMP_LINE_PREFIX_PATTERN.sub("", line.lstrip())
            line = MULTI_SPACE_PATTERN.sub(" ", line).strip()

            if not line or PAGE_MARKER_PATTERN.match(line):
                continue

            # Normalize "Speaker   :   text" to "Speaker: text" without touching the content.
            speaker_match = SPEAKER_PATTERN.match(line)
            if speaker_match:
                speaker, spoken = speaker_match.groups()
                speaker = speaker.strip()
                spoken = spoken.strip()
                line = f"{speaker}: {spoken}" if spoken else f"{speaker}:"

            # Drop consecutive duplicate lines produced by some transcription exporters.
            if cleaned_lines and cleaned_lines[-1] == line:
                continue

            cleaned_lines.append(line)

        cleaned_transcript = "\n".join(cleaned_lines).strip()

        if not cleaned_transcript:
            raise AgentExecutionError(
                AGENT_NAME,
                "Transcript contained no usable content after normalization."
            )

        logger.info(
            f"Parser Agent completed: {len(transcript_text)} chars -> "
            f"{len(cleaned_transcript)} chars across {len(cleaned_lines)} lines."
        )
        return cleaned_transcript
