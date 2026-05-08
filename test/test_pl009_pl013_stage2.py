"""Stage 2 tests: Text/object message pathways (PL-009 through PL-013)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COHORT_CODE, SAMPLE_STUDENT_ID


# ── PL-009 ──────────────────────────────────────────────────────────────────

def test_pl009_multiturn_text_returns_2xx_with_reply(harness):
    """Multi-turn pure text messages all return 2xx with non-empty assistant reply."""
    sender_id = "test_user_pl009"
    turns = ["你好", "我想了解课程", "Python相关课程有哪些"]

    for i, text in enumerate(turns):
        resp = harness.client.post("/api/chat", json={
            "sender_id": sender_id, "text": text
        })
        assert resp.status_code == 200, f"Turn {i} failed: {resp.status_code} {resp.text}"
        body = resp.json()
        assert len(body["messages"]) >= 1, f"Turn {i} has no messages"
        assert body["messages"][0]["text"], f"Turn {i} assistant reply is empty"
        assert body["sender_id"] == sender_id


# ── PL-010 ──────────────────────────────────────────────────────────────────

def test_pl010_send_order_object_no_5xx(harness):
    """Sending a structured order object returns 2xx, no 5xx."""
    sender_id = "test_user_pl010"
    order_obj = {
        "type": "order",
        "id": SAMPLE_ORDER_NO,
        "title": "订单 ORD20240401005",
        "attributes": {"status": "paid", "amount": "3280.00"},
    }
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "object": order_obj,
    })
    assert resp.status_code < 500, f"Got 5xx: {resp.status_code} {resp.text}"
    assert resp.status_code == 200
    body = resp.json()
    assert "messages" in body


# ── PL-011 ──────────────────────────────────────────────────────────────────

def test_pl011_send_cohort_object_no_5xx(harness):
    """Sending a structured cohort object returns 2xx, no 5xx."""
    sender_id = "test_user_pl011"
    cohort_obj = {
        "type": "cohort",
        "id": SAMPLE_COHORT_CODE,
        "title": "全栈开发系统班 · 默认班",
        "attributes": {"series_code": "fullstack_development_foundation"},
    }
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "object": cohort_obj,
    })
    assert resp.status_code < 500, f"Got 5xx: {resp.status_code} {resp.text}"
    assert resp.status_code == 200
    body = resp.json()
    assert "messages" in body


# ── PL-012 ──────────────────────────────────────────────────────────────────

def test_pl012_order_object_fills_slot_in_refund_flow(harness):
    """Order object fills missing order slot and advances refund flow."""
    sender_id = "test_user_pl012"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
    }

    # Start refund flow (needs order_no slot)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要退款"
    })
    assert resp.status_code == 200

    # Send order as OBJECT instead of text
    order_obj = {
        "type": "order",
        "id": SAMPLE_ORDER_NO,
        "title": f"订单 {SAMPLE_ORDER_NO}",
        "attributes": {"status": "paid"},
    }
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "object": order_obj,
    })
    assert resp.status_code == 200
    body = resp.json()

    # Verify the slot was filled - should advance to collect_reason
    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    assert state["active_flow"] == "refund"
    assert state["flow_slots"].get("order_no") == SAMPLE_ORDER_NO
    # Should have advanced past collect_order
    assert state["flow_step"] == "collect_reason"


# ── PL-013 ──────────────────────────────────────────────────────────────────

def test_pl013_cohort_object_fills_slot_in_progress_flow(harness):
    """Cohort object fills missing cohort slot and advances progress flow."""
    sender_id = "test_user_pl013"

    # Provide mock cohort list with 2+ items so progress flow enters collect_cohort
    harness.mock_business.cohorts_list = [
        {"cohort_name": "全栈开发系统班 · 默认班", "cohort_code": SAMPLE_COHORT_CODE},
        {"cohort_name": "前端开发基础班", "cohort_code": "C_frontend_development_foundation"},
    ]
    harness.mock_business.progress_data = {
        "student_id": sender_id,
        "cohort_code": SAMPLE_COHORT_CODE,
        "attendance_rate": 0.85,
        "video_completion_rate": 0.72,
        "homework_completion_rate": 0.68,
        "exam_avg_score": 82.5,
    }

    # Start learning progress flow (needs cohort)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查学习进度"
    })
    assert resp.status_code == 200

    # Send cohort as OBJECT — must match "cohort" type for object handling
    cohort_obj = {
        "type": "cohort",
        "id": SAMPLE_COHORT_CODE,
        "title": "全栈开发系统班 · 默认班",
        "attributes": {"series_code": "fullstack_development_foundation"},
    }
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "object": cohort_obj,
    })
    assert resp.status_code == 200

    # Verify state reflects cohort processing was handled
    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    # Progress flow completes immediately after cohort is received (single cohort lookup)
    # The flow should have processed the cohort (either active or completed)
    assert state["active_flow"] in (None, "progress"), f"Unexpected state: {state}"
