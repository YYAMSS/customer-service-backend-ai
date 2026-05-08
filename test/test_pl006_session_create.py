"""PL-006: Verify session creation via chat API returns valid sender_id + message_id."""
def test_pl006_chat_creates_session(harness):
    """Send a text message and verify the response contains sender_id and messages."""
    payload = {
        "sender_id": "test_user_pl006",
        "text": "你好",
    }
    response = harness.client.post("/api/chat", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["sender_id"] == "test_user_pl006"
    assert "message_id" in body
    assert "messages" in body
    assert len(body["messages"]) >= 1
    assert body["messages"][0]["text"] is not None
