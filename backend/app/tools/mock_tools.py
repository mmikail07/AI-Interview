from __future__ import annotations

from typing import Any, Callable

from ..schemas import Intent, ToolParameters

# Static datasets

_HOTELS: list[dict[str, Any]] = [
    {"id": "h1", "name": "Marina Bay Suites", "location": "Dubai", "price": 145, "rating": 4.2, "image": "https://placehold.co/400x240?text=Marina+Bay"},
    {"id": "h2", "name": "Desert Rose Hotel", "location": "Dubai", "price": 98, "rating": 3.9, "image": "https://placehold.co/400x240?text=Desert+Rose"},
    {"id": "h3", "name": "Palm Grand Resort", "location": "Dubai", "price": 320, "rating": 4.8, "image": "https://placehold.co/400x240?text=Palm+Grand"},
    {"id": "h4", "name": "Downtown Comfort Inn", "location": "Dubai", "price": 70, "rating": 3.5, "image": "https://placehold.co/400x240?text=Comfort+Inn"},
    {"id": "h5", "name": "Skyline Boutique", "location": "Dubai", "price": 210, "rating": 4.5, "image": "https://placehold.co/400x240?text=Skyline"},
    {"id": "h6", "name": "Riverside Lodge", "location": "London", "price": 160, "rating": 4.1, "image": "https://placehold.co/400x240?text=Riverside"},
    {"id": "h7", "name": "Westminster Stay", "location": "London", "price": 240, "rating": 4.6, "image": "https://placehold.co/400x240?text=Westminster"},
]

_FLIGHTS: list[dict[str, Any]] = [
    {"id": "f1", "airline": "Emirates", "origin": "Dubai", "destination": "London", "price": 540, "duration": "7h 35m", "stops": 0},
    {"id": "f2", "airline": "British Airways", "origin": "Dubai", "destination": "London", "price": 480, "duration": "7h 50m", "stops": 0},
    {"id": "f3", "airline": "Lufthansa", "origin": "Dubai", "destination": "London", "price": 395, "duration": "11h 10m", "stops": 1},
    {"id": "f4", "airline": "Qatar Airways", "origin": "Dubai", "destination": "Paris", "price": 510, "duration": "8h 05m", "stops": 1},
]


# Tool implementations

def _apply_sort(items: list[dict], sort: str | None) -> list[dict]:
    if sort == "price_asc":
        return sorted(items, key=lambda x: x["price"])
    if sort == "price_desc":
        return sorted(items, key=lambda x: x["price"], reverse=True)
    if sort == "rating_desc":
        return sorted(items, key=lambda x: x.get("rating", 0), reverse=True)
    return items


def hotel_tool(p: ToolParameters) -> dict[str, Any]:
    location = (p.location or "Dubai").strip()
    results = [h for h in _HOTELS if h["location"].lower() == location.lower()]
    if not results:  # unknown city -> fall back to Dubai
        location = "Dubai"
        results = [h for h in _HOTELS if h["location"] == "Dubai"]

    if p.max_price is not None:
        results = [h for h in results if h["price"] <= p.max_price]
    if p.min_rating is not None:
        results = [h for h in results if h["rating"] >= p.min_rating]
    results = _apply_sort(results, p.sort)

    return {"location": location, "count": len(results), "hotels": results,
            "applied": {"max_price": p.max_price, "min_rating": p.min_rating, "sort": p.sort}}


def flight_tool(p: ToolParameters) -> dict[str, Any]:
    results = list(_FLIGHTS)
    if p.origin:
        results = [f for f in results if f["origin"].lower() == p.origin.lower()]
    if p.destination:
        results = [f for f in results if f["destination"].lower() == p.destination.lower()]
    if p.max_price is not None:
        results = [f for f in results if f["price"] <= p.max_price]
    results = _apply_sort(results, p.sort)

    return {"origin": p.origin, "destination": p.destination, "date": p.date,
            "count": len(results), "flights": results}


def tracking_tool(p: ToolParameters) -> dict[str, Any]:
    order_id = p.order_id or "UNKNOWN"
    return {
        "order_id": order_id,
        "status": "In transit" if p.order_id else "Order id not found",
        "carrier": "FleetExpress",
        "eta": "2 days",
        "steps": [
            {"label": "Order placed", "done": True},
            {"label": "Packed", "done": True},
            {"label": "In transit", "done": bool(p.order_id)},
            {"label": "Out for delivery", "done": False},
            {"label": "Delivered", "done": False},
        ],
    }


def refund_tool(p: ToolParameters) -> dict[str, Any]:
    return {
        "order_id": p.order_id or "UNKNOWN",
        "refund_id": "RF-" + (p.order_id or "0000"),
        "status": "Refund initiated",
        "reason": p.reason or "Not specified",
        "amount_estimate": 0.0,
        "expected_days": 5,
    }


def complaint_tool(p: ToolParameters) -> dict[str, Any]:
    return {
        "ticket_id": "CMP-48217",
        "summary": p.note or p.reason or "General complaint",
        "status": "Logged",
        "priority": "Normal",
    }


def escalation_tool(p: ToolParameters) -> dict[str, Any]:
    return {
        "case_id": "ESC-90341",
        "topic": p.note or "General",
        "status": "Escalated to human agent",
        "queue_position": 3,
        "estimated_wait_minutes": 8,
    }


# Registry: intent -> (tool_name, handler)

ToolFn = Callable[[ToolParameters], dict[str, Any]]

TOOL_REGISTRY: dict[Intent, tuple[str, ToolFn]] = {
    Intent.hotel_search: ("hotel_tool", hotel_tool),
    Intent.flight_search: ("flight_tool", flight_tool),
    Intent.order_tracking: ("tracking_tool", tracking_tool),
    Intent.refund_request: ("refund_tool", refund_tool),
    Intent.complaint: ("complaint_tool", complaint_tool),
    Intent.escalation: ("escalation_tool", escalation_tool),
}


def run_tool(intent: Intent, params: ToolParameters) -> tuple[str | None, Any]:
    entry = TOOL_REGISTRY.get(intent)
    if entry is None:
        return None, None
    tool_name, fn = entry
    try:
        return tool_name, fn(params)
    except Exception as exc:  # a tool must never 500 the endpoint
        return tool_name, {"error": "tool_execution_failed", "detail": str(exc)}
