"""PL-007: Verify multi-turn session history maintains order and count."""
def test_pl007_session_history(harness):
    sender_id = "test_user_pl007"
    texts = ["你好，我想咨询课程", "全栈开发系统班怎么样？"]

    # Send 2 messages in the same session
    for text in texts:
        resp = harness.client.post("/api/chat", json={"sender_id": sender_id, "text": text})
        assert resp.status_code == 200, f"Chat failed: {resp.text}"

    # Fetch history
    resp = harness.client.get("/api/chat/history", params={"sender_id": sender_id})
    assert resp.status_code == 200, f"History failed: {resp.text}"
    body = resp.json()
    assert body["sender_id"] == sender_id
    messages = body["messages"]
    assert len(messages) >= 4, f"Expected at least 4 messages (2 user + 2 bot), got {len(messages)}"

    # Verify messages alternate user/bot and contain our text
    user_texts = [m["text"] for m in messages if m["role"] == "user"]
    assert len(user_texts) >= 2, f"Expected at least 2 user messages, got {len(user_texts)}"
    assert user_texts[0] == texts[0]
    assert user_texts[1] == texts[1]

    bot_texts = [m["text"] for m in messages if m["role"] == "bot"]
    assert len(bot_texts) >= 2, f"Expected at least 2 bot messages, got {len(bot_texts)}"
