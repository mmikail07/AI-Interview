from __future__ import annotations

import logging
import uuid

from ..memory import ConversationMemory
from ..schemas import (
    INTENT_TO_UI,
    ChatRequest,
    ChatResponse,
    ChatTurn,
    Intent,
    ToolParameters,
    UIType,
)
from ..tools import run_tool
from .intent_service import IntentService

logger = logging.getLogger(__name__)

# Default acknowledgements when the LLM/fallback didn't supply a reply.
_DEFAULT_REPLY: dict[Intent, str] = {
    Intent.order_tracking: "Here's the latest on your order.",
    Intent.refund_request: "I've started a refund for you.",
    Intent.complaint: "I'm sorry about that — your complaint has been logged.",
    Intent.escalation: "I'm connecting you with a human agent.",
    Intent.hotel_search: "Here are some hotels for you.",
    Intent.flight_search: "Here are some flights for you.",
    Intent.other: "How can I help with your order, a refund, hotels, or flights?",
}


class ChatService:
    def __init__(self, intent_service: IntentService, memory: ConversationMemory) -> None:
        self._intents = intent_service
        self._memory = memory

    async def handle(self, req: ChatRequest, request_id: str) -> ChatResponse:
        conversation_id = req.conversation_id or str(uuid.uuid4())

        history: list[ChatTurn] = self._memory.history(conversation_id) or req.history

        result, used_fallback = await self._intents.classify(req.message, history)
        logger.info(
            "rid=%s conv=%s intent=%s fallback=%s",
            request_id, conversation_id, result.intent.value, used_fallback,
        )

        params = self._merge_context(conversation_id, result.intent, result.parameters)

        tool_name, data = run_tool(result.intent, params)
        ui_type: UIType = INTENT_TO_UI.get(result.intent, UIType.text)
        message = result.reply or _DEFAULT_REPLY[result.intent]

        self._memory.add_user(conversation_id, req.message)
        self._memory.add_assistant(conversation_id, message)
        if result.intent in (Intent.hotel_search, Intent.flight_search):
            self._memory.set_context(conversation_id, result.intent, params)

        return ChatResponse(
            conversation_id=conversation_id,
            intent=result.intent,
            ui_type=ui_type,
            message=message,
            data=data,
            tool=tool_name,
            used_fallback=used_fallback,
        )

    def _merge_context(
        self, conversation_id: str, intent: Intent, params: ToolParameters
    ) -> ToolParameters:
        """Inherit unspecified slots from the previous search of the same kind.

        This is what makes "show cheaper ones" work: the new turn only carries
        ``sort=price_asc``; ``location`` is pulled forward from the last search.
        """
        if intent not in (Intent.hotel_search, Intent.flight_search):
            return params

        last_intent, last_params = self._memory.last_context(conversation_id)
        if last_intent != intent:
            return params

        merged = last_params.model_copy(deep=True)
        for fname, value in params.model_dump().items():
            if value is not None:
                setattr(merged, fname, value)
        return merged
