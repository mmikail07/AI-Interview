from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import get_settings
from .llm import OllamaClient
from .memory import ConversationMemory
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .services import ChatService, IntentService

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ollama = OllamaClient(settings)
    memory = ConversationMemory(max_turns=settings.max_history_turns)
    intent_service = IntentService(ollama)

    app.state.settings = settings
    app.state.ollama = ollama
    app.state.memory = memory
    app.state.chat_service = ChatService(intent_service, memory)

    reachable = await ollama.is_reachable()
    logger.info("Startup: model=%s ollama_reachable=%s", ollama.model, reachable)
    if not reachable:
        logger.warning("Ollama not reachable at %s — requests will use the rule-based fallback.",
                       settings.ollama_base_url)
    yield


app = FastAPI(title="Offline AI Support Assistant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    ollama: OllamaClient = request.app.state.ollama
    return HealthResponse(
        status="ok",
        ollama_reachable=await ollama.is_reachable(),
        model=ollama.model,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    return await _chat_service(request).handle(req, request.state.request_id)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    """SSE variant: emits coarse progress events, then the final result.

    The classification + tool call are not token-streamed (the contract is a
    single JSON object), so we stream *stages* — useful for a responsive UI that
    shows "thinking…" then "running tool…" before the widget appears.
    """
    service = _chat_service(request)
    request_id = request.state.request_id

    async def event_gen():
        def sse(event: str, payload: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

        yield sse("status", {"stage": "classifying"})
        response = await service.handle(req, request_id)
        yield sse("status", {"stage": "tool_complete", "tool": response.tool})
        yield sse("result", json.loads(response.model_dump_json()))
        yield sse("done", {})

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/reset")
async def reset(conversation_id: str, request: Request) -> dict:
    request.app.state.memory.reset(conversation_id)
    return {"status": "cleared", "conversation_id": conversation_id}
