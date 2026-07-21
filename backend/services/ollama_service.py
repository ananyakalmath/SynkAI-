"""
Ollama Service integration for SynkAI.
Provides direct HTTP communication with the local Ollama LLM service.
"""

import json
from typing import Any, Dict, Optional
import requests
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaService:
    """
    Service wrapper for interacting with local Ollama REST API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

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

    def generate(self, prompt: str, system_prompt: Optional[str] = None, json_format: bool = False) -> str:
        """
        Sends a generation request to Ollama `/api/generate` endpoint.

        Args:
            prompt (str): User prompt / transcript input.
            system_prompt (Optional[str]): Optional system context instruction.
            json_format (bool): Whether to request JSON output format from Ollama.

        Returns:
            str: Generated text response from LLM.

        Raises:
            ConnectionError: If Ollama server is unreachable.
            RuntimeError: If Ollama API returns an error response.
        """
        endpoint = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if json_format:
            payload["format"] = "json"

        logger.info(f"Sending request to Ollama ({self.model}) at {endpoint}...")

        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Failed to communicate with Ollama service at {endpoint}: {exc}")
            raise ConnectionError(
                f"Ollama server is unreachable at '{self.base_url}'. Please ensure Ollama is running and model '{self.model}' is available."
            ) from exc

        if response.status_code != 200:
            error_msg = f"Ollama API returned HTTP {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        data = response.json()
        raw_response = data.get("response", "").strip()

        if not raw_response:
            logger.warning("Ollama returned an empty response.")

        return raw_response
