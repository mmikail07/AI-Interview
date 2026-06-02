"""Typed API contract.

These Pydantic models are the single source of truth for what crosses the wire.
The backend *guarantees* a valid ``ChatResponse`` for every request: even when
the LLM is unreachable or returns garbage, the orchestration layer falls back to
a well-formed ``ui_type="text"`` payload (see ``services/chat_service.py``).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    user = "user"
    assistant = "assistant"


class Intent(str, Enum):
    order_tracking = "order_tracking"
    refund_request = "refund_request"
    complaint = "complaint"
    escalation = "escalation"
    hotel_search = "hotel_search"
    flight_search = "flight_search"
    other = "other"  # small-talk / unrecognised -> rendered as plain text


class UIType(str, Enum):
    """Drives which widget the Flutter client renders."""

    text = "text"
    hotel_list = "hotel_list"
    flight_list = "flight_list"
    order_status = "order_status"
    refund_status = "refund_status"
    complaint_ack = "complaint_ack"
    escalation = "escalation"


# Each intent maps deterministically to exactly one UI type.
INTENT_TO_UI: dict[Intent, UIType] = {
    Intent.order_tracking: UIType.order_status,
    Intent.refund_request: UIType.refund_status,
    Intent.complaint: UIType.complaint_ack,
    Intent.escalation: UIType.escalation,
    Intent.hotel_search: UIType.hotel_list,
    Intent.flight_search: UIType.flight_list,
    Intent.other: UIType.text,
}


class ChatTurn(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The latest user message.")
    conversation_id: Optional[str] = Field(
        default=None,
        description="Stable id for server-side memory. Omit on first turn to create one.",
    )
    # Optional client-supplied history. The server keeps its own memory keyed by
    # conversation_id, but accepting history makes the endpoint stateless-friendly
    # for clients that prefer to own the transcript.
    history: list[ChatTurn] = Field(default_factory=list)


class ToolParameters(BaseModel):
    """Slot-filled arguments extracted by the LLM and merged with prior context.

    Every field is optional; the LLM fills what the user provided and leaves the
    rest null. The chat service merges these with the previous search context so
    follow-ups like "show cheaper ones" inherit the earlier ``location``.
    """

    # travel (hotels / flights)
    location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    # "price_asc" | "price_desc" | "rating_desc"
    sort: Optional[str] = None
    # orders / refunds
    order_id: Optional[str] = None
    reason: Optional[str] = None
    note: Optional[str] = None


class IntentResult(BaseModel):
    """Structured output we force the LLM to produce."""

    intent: Intent
    parameters: ToolParameters = Field(default_factory=ToolParameters)
    reply: str = ""


class ChatResponse(BaseModel):
    conversation_id: str
    intent: Intent
    ui_type: UIType
    message: str = Field(..., description="Conversational text shown above any widget.")
    data: Any = Field(default=None, description="Tool payload; shape depends on ui_type.")
    tool: Optional[str] = Field(default=None, description="Name of the executed mock tool.")
    used_fallback: bool = Field(
        default=False,
        description="True when the LLM was unavailable/invalid and rule-based routing was used.",
    )


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    model: str
