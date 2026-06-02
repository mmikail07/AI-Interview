# Offline AI Support Assistant

A fully offline customer-support assistant. A FastAPI backend uses a local Ollama
model to classify the user's intent and extract parameters, runs a matching mock
tool, keeps short-term conversation memory, and returns strict JSON. A Flutter
client reads the `ui_type` field and renders the right widget for each response.

No cloud APIs are involved. After the one-time model pull the whole thing runs
without internet.

## How it works

1. The Flutter app sends `POST /chat` with the message and a `conversation_id`.
2. The backend builds a prompt (system + few-shot + recent history) and asks
   Ollama for a JSON object: an intent plus extracted parameters.
3. The intent maps to a mock tool, which returns static data. Memory is updated.
4. The response comes back as typed JSON with a `ui_type`.
5. The client switches on `ui_type` and renders a hotel list, order tracker,
   info card, or plain text.

If Ollama is unreachable or returns something invalid, a rule-based keyword
classifier takes over so the endpoint always responds with valid JSON.

## Project layout

```
ai-support-assistant/
├─ backend/
│  ├─ app/
│  │  ├─ main.py            # FastAPI routes: /chat, /chat/stream, /reset, /health
│  │  ├─ schemas.py         # Pydantic request/response models (the API contract)
│  │  ├─ config.py          # env-overridable settings (APP_ prefix)
│  │  ├─ memory.py          # in-memory short-term conversation store
│  │  ├─ llm/
│  │  │  ├─ ollama_client.py   # async client for the local Ollama REST API
│  │  │  └─ prompts.py         # system prompt, few-shot, JSON schema
│  │  ├─ services/
│  │  │  ├─ intent_service.py  # LLM classify + rule-based fallback
│  │  │  └─ chat_service.py    # orchestration + follow-up context merge
│  │  └─ tools/
│  │     └─ mock_tools.py      # the six mock tools + intent->tool registry
│  ├─ tests/test_chat.py    # offline tests (Ollama mocked)
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  └─ lib/
│     ├─ main.dart          # chat screen
│     ├─ models/            # ChatResponse / ChatMessage
│     ├─ services/          # http client
│     ├─ state/             # ChatProvider (provider package)
│     └─ widgets/           # widget_factory + hotel/flight/order/info widgets
└─ docker-compose.yml       # Ollama + backend together
```

## Prerequisites

- [Ollama](https://ollama.com) running locally
- Python 3.12+
- Flutter 3.x

## Run the backend

```bash
# 1. pull a model once (needs internet this one time)
ollama pull llama3.1

# 2. install and run
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. Settings can be overridden with
environment variables (or a `.env` file — see `backend/.env.example`):

```
APP_OLLAMA_BASE_URL=http://localhost:11434
APP_OLLAMA_MODEL=llama3.1
APP_MAX_HISTORY_TURNS=5
```

The first message after Ollama starts cold-loads the model, which can take about
a minute on CPU; later messages are fast. `request_timeout` defaults to 120s to
cover that — if Ollama is down or slower than the timeout, the request still
returns valid JSON through the rule-based fallback.

Run the tests (these mock Ollama, so they pass without a model):

```bash
cd backend
pytest
```

## Run the frontend

Only `lib/` is committed, so generate the platform folders first:

```bash
cd frontend
flutter create .        # creates android/ ios/ web/ etc.
flutter pub get
flutter run             # or: flutter run -d chrome
```

The backend URL defaults to `http://localhost:8000`. On an Android emulator the
host is reached through `10.0.2.2`, so run:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Run everything with Docker

```bash
docker compose up -d
docker compose exec ollama ollama pull llama3.1   # one time
```

Backend on `:8000`, Ollama on `:11434`.

## API

`POST /chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me hotels in Dubai under 200"}'
```

```json
{
  "conversation_id": "93b824b8-...",
  "intent": "hotel_search",
  "ui_type": "hotel_list",
  "message": "Here are hotels in Dubai under 200.",
  "data": {
    "location": "Dubai",
    "count": 3,
    "hotels": [
      {"id": "h1", "name": "Marina Bay Suites", "location": "Dubai", "price": 145, "rating": 4.2, "image": "..."}
    ]
  },
  "tool": "hotel_tool",
  "used_fallback": false
}
```

Follow-ups reuse the previous search context. Send the next message with the same
`conversation_id`:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show cheaper ones", "conversation_id": "93b824b8-..."}'
```

The server remembers the last hotel search, so "cheaper ones" keeps `location`
and just applies `sort=price_asc`.

Other endpoints:

- `POST /chat/stream` — same result, streamed as Server-Sent Events (status
  stages then the final payload).
- `POST /reset?conversation_id=...` — clear a conversation's memory.
- `GET /health` — liveness and whether Ollama is reachable.

## Intents and UI types

| Intent | Tool | ui_type | Widget |
| --- | --- | --- | --- |
| order_tracking | tracking_tool | order_status | OrderStatusWidget |
| refund_request | refund_tool | refund_status | InfoCardWidget |
| complaint | complaint_tool | complaint_ack | InfoCardWidget |
| escalation | escalation_tool | escalation | InfoCardWidget |
| hotel_search | hotel_tool | hotel_list | HotelWidget |
| flight_search | flight_tool | flight_list | FlightWidget |
| other | — | text | plain bubble |

## Design notes

- **One source of truth for the contract.** Every response is a Pydantic
  `ChatResponse`, and intents map to `ui_type` through a single table
  (`INTENT_TO_UI`). The client never parses loose maps.
- **Deterministic routing.** The model is asked for structured output via
  Ollama's `format` JSON schema at `temperature=0`, then validated with Pydantic.
  Intents map to tools through a registry, so adding a new capability is a tool
  function plus two table entries.
- **Always responds.** A keyword classifier backs up the LLM, so an outage or a
  bad model response still produces a valid, typed answer.
- **Short-term memory.** A per-conversation store keeps the last few turns and
  the most recent search parameters, which is what makes follow-ups work.
- **Extensible UI.** `WidgetFactory` switches on `ui_type`; a new screen is one
  more `case`.

## Offline note

The mock hotel data uses remote placeholder image URLs. With no internet the
images simply fall back to a local icon — everything else works offline.

## Screenshots

The Flutter web client talking to the local backend.

Greeting, a flight search, a "show cheaper ones" follow-up, then a hotel search —
each answer rendered as its own widget:

![Conversation](screenshots/conversation.png)

Hotel results with star ratings and prices; the model picked up "at least 4 stars"
straight from the sentence:

![Hotel results](screenshots/hotel-results.png)

The empty state, shown when nothing matches the filters:

![No matches](screenshots/empty-state.png)
