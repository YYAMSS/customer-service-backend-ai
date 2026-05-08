"""PL-008: Verify session state API shows active task and filled slots."""
def test_pl008_session_state_shows_active_task(harness):
    sender_id = "test_user_pl008"

    # Trigger refund flow which sets active_flow and collect_order step
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要退款"
    })
    assert resp.status_code == 200

    # Fetch state
    resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    assert resp.status_code == 200, f"State API failed: {resp.text}"
    state = resp.json()
    assert state["sender_id"] == sender_id
    assert state["active_flow"] is not None, f"Expected active_flow, got: {state}"

    # Flow slots should exist (possibly empty at this stage)
    assert "flow_slots" in state
    assert isinstance(state["flow_slots"], dict)


def test_pl008_session_state_after_slot_fill(harness):
    sender_id = "test_user_pl008b"

    # Provide mock order data so _safe_order succeeds
    harness.mock_business.order_data = {
        "order_no": "ORD20240401005",
        "order_status": "paid",
        "amount": "3280.00",
    }

    # Start refund flow
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要退款"
    })
    assert resp.status_code == 200

    # Provide order number (the refund flow collect_order step)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "ORD20240401005"
    })
    assert resp.status_code == 200

    # Fetch state - should have order_no slot filled
    resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    assert resp.status_code == 200
    state = resp.json()
    assert state["active_flow"] == "refund"
    slots = state["flow_slots"]
    assert "order_no" in slots, f"Expected 'order_no' in slots, got: {slots}"
    assert slots["order_no"] == "ORD20240401005"
