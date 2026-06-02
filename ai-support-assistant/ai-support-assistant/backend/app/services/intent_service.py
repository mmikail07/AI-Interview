"""Intent classification service.

Primary path: ask the local LLM (Ollama) for structured ``IntentResult``.
Fallback path: a deterministic keyword classifier used when Ollama is
unreachable or returns something invalid. The fallback keeps the API contract
intact (the endpoint always responds) and makes the demo runnable even before a
model is pulled.
"""

from __future__ import annotations

import logging
import re

from pydantic import ValidationError

from ..llm import OllamaClient, OllamaError
from ..llm.prompts import build_messages
from ..schemas import ChatTurn, Intent, IntentResult, ToolParameters

logger = logging.getLogger(__name__)


_KEYWORDS: list[tuple[Intent, tuple[str, ...]]] = [
    (Intent.escalation, ("human", "agent", "manager", "escalate", "representative", "supervisor")),
    (Intent.refund_request, ("refund", "money back", "return", "reimburse")),
    (Intent.order_tracking, ("track", "where is my order", "order status", "package", "parcel", "delivery")),
    (Intent.hotel_search, ("hotel", "hotels", "room", "stay", "resort", "accommodation")),
    (Intent.flight_search, ("flight", "flights", "fly", "airline", "ticket to")),
    (Intent.complaint, ("complain", "complaint", "terrible", "awful", "angry", "furious", "disappointed", "worst")),
]

_ORDER_RE = re.compile(r"#?\b([A-Z]{0,2}\d{3,})\b")
_PRICE_RE = re.compile(r"(?:under|below|less than|max)\s*\$?(\d+)", re.IGNORECASE)


class IntentService:
    def __init__(self, ollama: OllamaClient) -> None:
        self._ollama = ollama

    async def classify(self, message: str, history: list[ChatTurn]) -> tuple[IntentResult, bool]:
        """Return ``(result, used_fallback)``."""
        messages = build_messages(message, history)
        try:
            raw = await self._ollama.classify(messages)
            result = IntentResult.model_validate(raw)
            return result, False
        except (OllamaError, ValidationError) as exc:
            logger.warning("Falling back to rule-based classifier: %s", exc)
            return self._fallback(message), True

    # ------------------------------------------------------------------ #
    @staticmethod
    def _fallback(message: str) -> IntentResult:
        text = message.lower()
        intent = Intent.other

        # "cheaper" with no other signal is a travel follow-up; let the chat
        # service merge it onto the previous search context.
        cheaper = any(w in text for w in ("cheaper", "cheapest", "lower price"))

        for candidate, words in _KEYWORDS:
            if any(w in text for w in words):
                intent = candidate
                break
        if intent is Intent.other and cheaper:
            intent = Intent.hotel_search  # best-effort; merged with last context

        params = ToolParameters()
        if cheaper:
            params.sort = "price_asc"

        if intent in (Intent.order_tracking, Intent.refund_request):
            m = _ORDER_RE.search(message)
            if m:
                params.order_id = m.group(1)

        if intent in (Intent.hotel_search, Intent.flight_search):
            pm = _PRICE_RE.search(message)
            if pm:
                params.max_price = float(pm.group(1))

        if intent is Intent.complaint:
            params.note = message[:140]

        return IntentResult(intent=intent, parameters=params,
                            reply="")  # reply filled by chat service
