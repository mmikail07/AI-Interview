"""Prompt engineering for intent classification + slot filling.

Strategy
--------
1. **Forced structured output.** We pass a JSON Schema to Ollama's ``format``
   field (structured outputs, Ollama >= 0.5). Combined with ``temperature=0``
   this makes the model emit *only* a JSON object matching ``IntentResult`` —
   no markdown fences, no prose. This is the backbone of deterministic routing.
2. **Tight task framing.** The system prompt enumerates the intents with crisp
   descriptions and the exact parameter slots to fill, so the model classifies
   rather than free-associates.
3. **Few-shot anchoring.** A handful of examples lock in the output shape and,
   crucially, demonstrate *follow-up resolution* ("show cheaper ones" ->
   ``sort: price_asc``) so context carried in the message history is used.
"""

from __future__ import annotations

from .. import schemas
from ..schemas import ChatTurn, Role

# JSON Schema handed to Ollama's `format` parameter. Mirrors IntentResult.
INTENT_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [i.value for i in schemas.Intent],
        },
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": ["string", "null"]},
                "origin": {"type": ["string", "null"]},
                "destination": {"type": ["string", "null"]},
                "date": {"type": ["string", "null"]},
                "max_price": {"type": ["number", "null"]},
                "min_rating": {"type": ["number", "null"]},
                "sort": {"type": ["string", "null"]},
                "order_id": {"type": ["string", "null"]},
                "reason": {"type": ["string", "null"]},
                "note": {"type": ["string", "null"]},
            },
        },
        "reply": {"type": "string"},
    },
    "required": ["intent", "parameters", "reply"],
}


SYSTEM_PROMPT = """You are the routing brain of an offline customer-support assistant.
Your ONLY job is to read the latest user message (in the context of the recent \
conversation) and return a JSON object that classifies the request and extracts \
parameters. Do not answer the user's question yourself — a downstream tool does that.

Choose exactly one intent:
- order_tracking : user asks where their order/parcel/package is, delivery status. Extract order_id if present.
- refund_request : user wants a refund / money back / return. Extract order_id and reason if present.
- complaint      : user is unhappy about a product/service but is not (yet) asking to escalate or refund. Put a short summary in parameters.note.
- escalation     : user explicitly wants a human agent / manager / to escalate. Put the topic in parameters.note.
- hotel_search   : user wants to find/book/see hotels. Extract location, max_price, min_rating, sort.
- flight_search  : user wants flights. Extract origin, destination, date, max_price, sort.
- other          : greetings, thanks, small talk, or anything not covered above.

Rules for the `parameters` object:
- Fill ONLY the fields the user actually provided (across the recent conversation). Leave everything else null.
- `sort` must be one of: "price_asc", "price_desc", "rating_desc", or null.
- Resolve follow-ups using prior turns. If the user previously searched hotels in Dubai \
and now says "show cheaper ones", keep intent=hotel_search and set sort="price_asc" \
(carry the earlier location forward only if you can infer it; otherwise leave location null \
and the server will reuse it).

The `reply` field is a short, friendly one-sentence acknowledgement (e.g. "Here are hotels in Dubai.").

Respond with JSON only."""


# Few-shot examples. Kept as plain (user, assistant-json) pairs that we splice
# into the message list ahead of the live turn.
_FEWSHOT: list[tuple[str, str]] = [
    (
        "Where is my order #A1023?",
        '{"intent":"order_tracking","parameters":{"order_id":"A1023"},"reply":"Let me check the status of order A1023 for you."}',
    ),
    (
        "I want a refund for order 5567, it arrived broken",
        '{"intent":"refund_request","parameters":{"order_id":"5567","reason":"arrived broken"},"reply":"I\'ve started a refund for order 5567."}',
    ),
    (
        "This is the third time your app crashed, I am furious",
        '{"intent":"complaint","parameters":{"note":"app repeatedly crashing"},"reply":"I\'m sorry about the crashes — I\'ve logged your complaint."}',
    ),
    (
        "Just connect me to a human agent already",
        '{"intent":"escalation","parameters":{"note":"requested human agent"},"reply":"Connecting you to a human agent."}',
    ),
    (
        "Show me hotels in Dubai under 200 a night",
        '{"intent":"hotel_search","parameters":{"location":"Dubai","max_price":200},"reply":"Here are hotels in Dubai under 200."}',
    ),
    # follow-up: relies on prior context -> only sets sort
    (
        "show cheaper ones",
        '{"intent":"hotel_search","parameters":{"sort":"price_asc"},"reply":"Here are some cheaper options."}',
    ),
    (
        "find flights from Dubai to London on Friday",
        '{"intent":"flight_search","parameters":{"origin":"Dubai","destination":"London","date":"Friday"},"reply":"Here are flights from Dubai to London."}',
    ),
    (
        "thanks!",
        '{"intent":"other","parameters":{},"reply":"You\'re welcome! Anything else I can help with?"}',
    ),
]


def build_messages(message: str, history: list[ChatTurn]) -> list[dict]:
    """Assemble the Ollama chat message list: system + few-shot + recent history + current turn."""
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for user_text, assistant_json in _FEWSHOT:
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": assistant_json})

    for turn in history:
        # The model only needs the textual transcript to resolve references.
        role = "assistant" if turn.role == Role.assistant else "user"
        messages.append({"role": role, "content": turn.content})

    messages.append({"role": "user", "content": message})
    return messages
