"""Thin async client for the local Ollama REST API.

Only the local ``/api/chat`` (structured) and ``/api/tags`` (health) endpoints
are used. No external/cloud calls are ever made — fully offline by design.
"""

from __future__ import annotations

import json
import logging

import httpx

from ..config import Settings
from .prompts import INTENT_JSON_SCHEMA

logger = logging.getLogger(__name__)


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable or returns an unusable response."""


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._temperature = settings.ollama_temperature
        self._timeout = settings.request_timeout

    @property
    def model(self) -> str:
        return self._model

    async def is_reachable(self) -> bool:
        """Cheap liveness probe used by /health."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def classify(self, messages: list[dict]) -> dict:
        """Send the prompt and return the parsed JSON object.

        Forces structured output via the ``format`` JSON schema and pins
        ``temperature`` for deterministic routing. Raises ``OllamaError`` on any
        transport, status, or JSON problem so the caller can fall back cleanly.
        """
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "format": INTENT_JSON_SCHEMA,
            "options": {"temperature": self._temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:  # connection refused, timeout, 4xx/5xx
            raise OllamaError(f"Ollama request failed: {exc}") from exc

        content = (body.get("message") or {}).get("content", "")
        if not content:
            raise OllamaError("Ollama returned an empty message.")

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("Ollama returned non-JSON content: %r", content[:200])
            raise OllamaError("Ollama returned invalid JSON.") from exc
