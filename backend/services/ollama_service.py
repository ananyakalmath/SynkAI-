"""
Ollama Service integration for SynkAI.
Provides direct HTTP communication with the local Ollama LLM service.

Two properties make this reliable against a local Ollama server:

1. All generation requests pass through the shared process-wide Ollama concurrency gate, so
   a single local server is never asked to run more generations than it can handle.
2. Responses are streamed and reassembled. The HTTP read timeout therefore measures the gap
   between tokens (a stalled server) instead of total generation time, so a slow-but-healthy
   local model is not killed mid-answer. A separate wall-clock deadline still bounds the call.
"""

import json
import re
import time
from typing import Any, Dict, Optional
import requests
from backend.config import settings
from backend.services.ollama_gate import ollama_gate
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Some reasoning models (qwen3) may still emit inline <think> blocks depending on version.
THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)

# Set once per process if the server rejects the `think` parameter for the configured model.
_THINK_PARAM_UNSUPPORTED = False


class OllamaService:
    """
    Service wrapper for interacting with local Ollama REST API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT

    def check_health(self) -> bool:
        """
        Verifies if local Ollama server is reachable.

        Returns:
            bool: True if Ollama service responds, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception as exc:
            logger.warning(f"Ollama health check failed at {self.base_url}: {exc}")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_format: bool = False,
        label: Optional[str] = None
    ) -> str:
        """
        Sends a generation request to Ollama `/api/generate`.

        The call waits for a free slot on the shared Ollama gate before issuing the HTTP
        request, which keeps local inference sequential (and therefore predictable) instead
        of letting several qwen3 generations fight over the same CPU/GPU.

        Args:
            prompt (str): User prompt / transcript input.
            system_prompt (Optional[str]): Optional system context instruction.
            json_format (bool): Whether to request JSON output format from Ollama.
            label (Optional[str]): Caller name used in logs (e.g. the agent name).

        Returns:
            str: Generated text response from LLM.

        Raises:
            OllamaBusyError: If no inference slot became available in time.
            ConnectionError: If Ollama is unreachable, stalled, or exceeded the deadline.
            RuntimeError: If Ollama API returns an error response.
        """
        caller = label or f"ollama:{self.model}"

        with ollama_gate.slot(caller):
            raw_response = self._post_generate(prompt, system_prompt, json_format, caller)

        cleaned = THINK_BLOCK_PATTERN.sub("", raw_response).strip()

        if not cleaned:
            logger.warning(f"Ollama returned an empty response for '{caller}'.")

        return cleaned

    def _post_generate(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_format: bool,
        caller: str
    ) -> str:
        """
        Issues the HTTP request to Ollama. Assumes an inference slot is already held.
        """
        global _THINK_PARAM_UNSUPPORTED

        endpoint = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            # Streamed so `self.timeout` measures token-to-token silence, not total runtime.
            "stream": True,
            # Keeping the model resident avoids paying the multi-second model load cost
            # again for every agent in the workflow.
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": 0.2,
                # Upper bound on generated tokens. Local inference cost is dominated by
                # output length, so this keeps a single agent from running away and
                # burning the whole read timeout.
                "num_predict": settings.OLLAMA_NUM_PREDICT
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if json_format:
            payload["format"] = "json"

        # Thinking mode roughly triples-to-16x the latency of a qwen3 call for no benefit on
        # these extraction tasks, which is a large part of why agents used to time out.
        disable_thinking = not settings.OLLAMA_ENABLE_THINKING and not _THINK_PARAM_UNSUPPORTED
        if disable_thinking:
            payload["think"] = False

        logger.info(
            f"Sending request to Ollama ({self.model}) for '{caller}' "
            f"[stall_timeout={self.timeout}s, deadline={settings.OLLAMA_MAX_DURATION}s, "
            f"thinking={'off' if disable_thinking else 'on'}]..."
        )

        started = time.monotonic()

        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout, stream=True)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to communicate with Ollama service at {endpoint}: {exc}")
            raise ConnectionError(
                f"Ollama server is unreachable at '{self.base_url}'. Please ensure Ollama is running and model '{self.model}' is available."
            ) from exc

        with response:
            # Older Ollama builds / non-reasoning models reject the `think` parameter.
            if response.status_code == 400 and disable_thinking and "think" in response.text.lower():
                logger.warning(
                    f"Ollama rejected the 'think' parameter for model '{self.model}'. "
                    "Retrying without it and disabling the parameter for this process."
                )
                _THINK_PARAM_UNSUPPORTED = True
                return self._post_generate(prompt, system_prompt, json_format, caller)

            if response.status_code != 200:
                error_msg = f"Ollama API returned HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            text = self._consume_stream(response, caller, started)

        logger.info(f"Ollama completed '{caller}' in {time.monotonic() - started:.1f}s.")
        return text.strip()

    def _consume_stream(self, response: requests.Response, caller: str, started: float) -> str:
        """
        Reassembles a streamed `/api/generate` response into a single string.

        Args:
            response (requests.Response): Streaming response with an open body.
            caller (str): Caller name used in error messages and logs.
            started (float): `time.monotonic()` value captured before the request.

        Returns:
            str: Concatenated generated text.

        Raises:
            ConnectionError: If the stream stalls or the wall-clock deadline is exceeded.
            RuntimeError: If Ollama reports an error mid-stream.
        """
        chunks = []
        deadline = settings.OLLAMA_MAX_DURATION

        try:
            for line in response.iter_lines(decode_unicode=True):
                elapsed = time.monotonic() - started
                if elapsed > deadline:
                    raise ConnectionError(
                        f"Ollama generation for '{caller}' exceeded the {deadline}s deadline "
                        f"(produced {len(''.join(chunks))} characters). Consider a smaller "
                        f"OLLAMA_MODEL for this machine."
                    )

                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping unparseable stream line from Ollama for '{caller}'.")
                    continue

                if event.get("error"):
                    raise RuntimeError(f"Ollama reported an error for '{caller}': {event['error']}")

                chunks.append(event.get("response") or "")

                if event.get("done"):
                    break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            # `requests` surfaces a mid-stream read timeout as ConnectionError, so both
            # cases mean the same thing here: the server went quiet on us.
            logger.error(
                f"Ollama stream for '{caller}' produced no output for {self.timeout}s "
                f"(after {time.monotonic() - started:.1f}s total): {exc}"
            )
            raise ConnectionError(
                f"Ollama stopped responding while running '{caller}': no output for {self.timeout}s. "
                f"Check that the Ollama server is healthy and that '{self.model}' fits in memory."
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"Ollama stream for '{caller}' failed: {exc}")
            raise ConnectionError(
                f"Connection to Ollama was lost while running '{caller}': {exc}"
            ) from exc

        return "".join(chunks)
