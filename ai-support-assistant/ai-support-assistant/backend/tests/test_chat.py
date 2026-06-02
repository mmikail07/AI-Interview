import pytest
from fastapi.testclient import TestClient

from app.llm import OllamaError
from app.main import app
from app.schemas import ToolParameters
from app.tools import run_tool
from app.schemas import Intent


@pytest.fixture
def client(monkeypatch):
    # Build the app's lifespan-managed state by entering the TestClient context.
    with TestClient(app) as c:
        yield c


def _patch_llm(monkeypatch, client, response: dict | None = None, raise_error: bool = False):
    ollama = client.app.state.ollama

    async def fake_classify(messages):
        if raise_error:
            raise OllamaError("simulated outage")
        return response

    monkeypatch.setattr(ollama, "classify", fake_classify)
    # health probe should not hit the network either
    async def fake_reachable():
        return not raise_error
    monkeypatch.setattr(ollama, "is_reachable", fake_reachable)


def test_hotel_tool_sorts_and_filters():
    name, data = run_tool(Intent.hotel_search,
                          ToolParameters(location="Dubai", max_price=200, sort="price_asc"))
    prices = [h["price"] for h in data["hotels"]]
    assert prices == sorted(prices)
    assert all(p <= 200 for p in prices)
    assert name == "hotel_tool"


def test_chat_hotel_then_cheaper_followup(monkeypatch, client):
    # First turn: hotels in Dubai
    _patch_llm(monkeypatch, client, {
        "intent": "hotel_search",
        "parameters": {"location": "Dubai"},
        "reply": "Here are hotels in Dubai.",
    })
    r1 = client.post("/chat", json={"message": "show hotels in Dubai"})
    assert r1.status_code == 200
    body1 = r1.json()
    conv = body1["conversation_id"]
    assert body1["ui_type"] == "hotel_list"
    assert body1["data"]["location"] == "Dubai"

    # Second turn: "cheaper ones" -> only sort provided; location inherited
    _patch_llm(monkeypatch, client, {
        "intent": "hotel_search",
        "parameters": {"sort": "price_asc"},
        "reply": "Cheaper options:",
    })
    r2 = client.post("/chat", json={"message": "show cheaper ones", "conversation_id": conv})
    body2 = r2.json()
    assert body2["data"]["location"] == "Dubai"  # context carried forward
    prices = [h["price"] for h in body2["data"]["hotels"]]
    assert prices == sorted(prices)


def test_fallback_when_llm_down(monkeypatch, client):
    _patch_llm(monkeypatch, client, raise_error=True)
    r = client.post("/chat", json={"message": "I need a refund for order #A1023"})
    body = r.json()
    assert body["used_fallback"] is True
    assert body["intent"] == "refund_request"
    assert body["ui_type"] == "refund_status"
    assert body["data"]["order_id"] == "A1023"


def test_other_intent_renders_text(monkeypatch, client):
    _patch_llm(monkeypatch, client, {
        "intent": "other", "parameters": {}, "reply": "Hi there!",
    })
    r = client.post("/chat", json={"message": "hello"})
    body = r.json()
    assert body["ui_type"] == "text"
    assert body["data"] is None
