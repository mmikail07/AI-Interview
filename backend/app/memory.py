from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from .schemas import ChatTurn, Intent, Role, ToolParameters


@dataclass
class _Conversation:
    turns: deque[ChatTurn]
    last_intent: Optional[Intent] = None
    last_params: ToolParameters = field(default_factory=ToolParameters)


class ConversationMemory:
    def __init__(self, max_turns: int = 5) -> None:
        # store up to max_turns * 2 messages (user+assistant per turn)
        self._max_messages = max_turns * 2
        self._store: dict[str, _Conversation] = defaultdict(
            lambda: _Conversation(turns=deque(maxlen=self._max_messages))
        )

    def history(self, conversation_id: str) -> list[ChatTurn]:
        return list(self._store[conversation_id].turns)

    def last_context(self, conversation_id: str) -> tuple[Optional[Intent], ToolParameters]:
        conv = self._store[conversation_id]
        return conv.last_intent, conv.last_params

    def add_user(self, conversation_id: str, text: str) -> None:
        self._store[conversation_id].turns.append(ChatTurn(role=Role.user, content=text))

    def add_assistant(self, conversation_id: str, text: str) -> None:
        self._store[conversation_id].turns.append(ChatTurn(role=Role.assistant, content=text))

    def set_context(self, conversation_id: str, intent: Intent, params: ToolParameters) -> None:
        conv = self._store[conversation_id]
        conv.last_intent = intent
        conv.last_params = params

    def reset(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)
