"""
Shared JSON extraction helper for SynkAI Sprint 4 agents.

Each specialized agent keeps its own prompt, its own output key and its own class; this
helper only holds the mechanics they all share (one gated Ollama call, strict JSON parsing,
and explicit failure reporting) so no agent can silently turn an error into an empty list.
"""

import json
from typing import Any, List
from backend.agents.errors import AgentExecutionError
from backend.services.ollama_service import OllamaService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def run_json_list_extraction(
    ollama: OllamaService,
    agent_name: str,
    system_prompt: str,
    parsed_transcript: str,
    result_key: str
) -> List[Any]:
    """
    Runs a single JSON-mode LLM extraction and returns the list stored under `result_key`.

    Args:
        ollama (OllamaService): LLM client to use.
        agent_name (str): Name of the calling agent, used for logs and error reporting.
        system_prompt (str): Agent-specific extraction instructions.
        parsed_transcript (str): Cleaned transcript produced by the Parser Agent.
        result_key (str): Key holding the result list in the LLM's JSON object.

    Returns:
        List[Any]: Extracted items (empty only when the LLM genuinely found nothing).

    Raises:
        AgentExecutionError: If the transcript is empty, the LLM call fails, or the
            response is not a JSON object containing a list under `result_key`.
    """
    if not parsed_transcript or not parsed_transcript.strip():
        raise AgentExecutionError(agent_name, "Received an empty transcript.")

    try:
        raw_response = ollama.generate(
            prompt=parsed_transcript,
            system_prompt=system_prompt,
            json_format=True,
            label=agent_name
        )
    except Exception as exc:
        logger.error(f"{agent_name} LLM call failed: {exc}")
        raise AgentExecutionError(agent_name, str(exc)) from exc

    try:
        data = json.loads(raw_response.strip())
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.error(f"{agent_name} could not parse LLM JSON output: {exc}")
        raise AgentExecutionError(
            agent_name,
            f"LLM returned output that is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise AgentExecutionError(agent_name, "LLM returned JSON that is not an object.")

    items = data.get(result_key, [])
    if items is None:
        items = []

    if not isinstance(items, list):
        raise AgentExecutionError(
            agent_name,
            f"Expected a list under '{result_key}' but received {type(items).__name__}."
        )

    logger.info(f"{agent_name} completed successfully. Extracted {len(items)} item(s).")
    return items
