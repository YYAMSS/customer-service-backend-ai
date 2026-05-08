"""
PL-003, PL-004, PL-005: HTTP client wrappers for the edu chat backend.

PL-003: httpx.AsyncClient wrapper with timeout and error body parsing.
PL-004: Non-streaming chat request helper.
PL-005: Streaming SSE chat request helper.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from test.test_config import API_CHAT, API_CHAT_HISTORY

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def create_client(timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    """PL-003: Create an HTTP client with timeout and error body parsing support."""
    return httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT)


async def parse_response(response: httpx.Response) -> dict[str, Any]:
    """PL-003: Parse response body, raising on HTTP errors with body detail."""
    if response.is_error:
        detail = None
        try:
            body = response.json()
            detail = body.get("detail", body)
        except Exception:
            body_text = response.text[:500]
            detail = body_text if body_text else None
        raise httpx.HTTPStatusError(
            f"HTTP {response.status_code}: {detail}",
            request=response.request,
            response=response,
        )
    return response.json()


async def send_chat_request(
    client: httpx.AsyncClient,
    sender_id: str,
    text: str | None = None,
    obj: dict[str, Any] | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    """PL-004: Send a non-streaming chat request and return the parsed response."""
    payload: dict[str, Any] = {"sender_id": sender_id}
    if text is not None:
        payload["text"] = text
    if obj is not None:
        payload["object"] = obj
    if message_id is not None:
        payload["message_id"] = message_id
    response = await client.post(API_CHAT, json=payload)
    return await parse_response(response)


async def send_chat_request_stream(
    client: httpx.AsyncClient,
    sender_id: str,
    text: str | None = None,
    obj: dict[str, Any] | None = None,
    message_id: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """PL-005: Send a streaming SSE chat request, return (full_text, events).

    The service may or may not support SSE; this handles both SSE streaming
    and plain JSON fallback.
    """
    payload: dict[str, Any] = {"sender_id": sender_id}
    if text is not None:
        payload["text"] = text
    if obj is not None:
        payload["object"] = obj
    if message_id is not None:
        payload["message_id"] = message_id

    response = await client.post(API_CHAT, json=payload)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        events = []
        full_text = ""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    events.append(event)
                    for msg in event.get("messages", []):
                        if msg.get("text"):
                            full_text += msg["text"]
                except json.JSONDecodeError:
                    continue
        return full_text, events
    else:
        # Non-streaming fallback
        body = response.json()
        text_parts = []
        for msg in body.get("messages", []):
            if msg.get("text"):
                text_parts.append(msg["text"])
        return "".join(text_parts), [body]


async def get_chat_history(
    client: httpx.AsyncClient,
    sender_id: str,
) -> dict[str, Any]:
    """Fetch chat history for a sender."""
    response = await client.get(API_CHAT_HISTORY, params={"sender_id": sender_id})
    return await parse_response(response)
