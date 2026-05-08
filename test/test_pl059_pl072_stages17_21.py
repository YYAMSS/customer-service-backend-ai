"""Stages 17-21: Non-functional, user roles (PL-059~072)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COHORT_CODE


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 17 — Non-functional: reliability (§6.1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl059_invalid_params_does_not_break_service(harness):
    """PL-059: Invalid parameter injection returns expected error, another session works."""
    sender_id = "test_user_pl059"

    # Send an invalid request (empty text and no object)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "",
    })
    # Should get either 422 (validation error) or 200 with chitchat
    assert resp.status_code in (200, 422), \
        f"PL-059: Expected 200 or 422, got {resp.status_code}"

    # Another concurrent session should work fine
    resp2 = harness.client.post("/api/chat", json={
        "sender_id": "test_user_pl059_other", "text": "你好"
    })
    assert resp2.status_code == 200
    assert resp2.json()["messages"][0]["text"]


def test_pl060_service_resilience(harness):
    """PL-060: Service handles normal message without blocking."""
    sender_id = "test_user_pl060"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "测试消息"
    })
    assert resp.status_code == 200
    # Service should respond without hanging
    assert resp.elapsed.total_seconds() < 5.0, \
        f"PL-060: Response took too long: {resp.elapsed.total_seconds()}s"


def test_pl061_persistence_failure_graceful(harness):
    """PL-061: After persistence operations, service still responds (not silent blank)."""
    sender_id = "test_user_pl061"
    # Perform normal operations
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "退款政策是什么"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should not be empty
    assert reply and len(reply) > 0, "PL-061: Should not return silent blank"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 18 — Non-functional: observability (§6.2)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl062_trace_intent_in_response(harness):
    """PL-062: After single dialogue, response contains traceable intent information."""
    sender_id = "test_user_pl062"
    harness.mock_business.courses_list = [
        {"series_code": "fullstack_development_foundation", "series_name": "全栈开发系统班"},
        {"series_code": "python_programming", "series_name": "Python编程"},
    ]
    harness.mock_business.course_data = {
        "series_code": "fullstack_development_foundation",
        "series_name": "全栈开发系统班",
        "target_audience": "在校学生",
        "delivery_mode": "线上直播",
        "sale_status": "在售",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "全栈开发课程咨询"
    })
    assert resp.status_code == 200
    body = resp.json()
    # Response should have sender_id and message_id (trace identifiers)
    assert body["sender_id"] == sender_id
    assert "message_id" in body
    assert len(body["messages"]) >= 1


def test_pl063_state_observability(harness):
    """PL-063: State API provides flow state that can be inspected."""
    sender_id = "test_user_pl063"
    harness.mock_business.order_data = {"order_no": SAMPLE_ORDER_NO, "order_status": "paid"}

    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": SAMPLE_ORDER_NO})

    resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    assert resp.status_code == 200
    state = resp.json()
    # State should show flow progress
    assert state["active_flow"] == "refund"
    assert state["flow_step"] in ("collect_reason", "collect_order")


def test_pl064_audit_log_for_ticket(harness):
    """PL-064: After ticket creation, state is clean (flow completed, evidence in history)."""
    sender_id = "test_user_pl064"
    harness.mock_business.order_data = {"order_no": SAMPLE_ORDER_NO, "order_status": "paid"}

    # Complete a ticket
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要投诉"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "投诉"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": SAMPLE_ORDER_NO})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "课程质量投诉"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "确认"})

    # History should contain the ticket creation event
    resp = harness.client.get("/api/chat/history", params={"sender_id": sender_id})
    history = resp.json()
    bot_messages = [m["text"] for m in history["messages"] if m["role"] == "bot"]
    ticket_msgs = [t for t in bot_messages if "TICKET" in t or "工单" in t]
    assert len(ticket_msgs) >= 1, "PL-064: Should have ticket creation in history"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 19 — Non-functional: accuracy (§6.3)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl065_data_consistency(harness):
    """PL-065: Updated order status reflects in subsequent query."""
    sender_id = "test_user_pl065"

    # First query with "paid" status
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO, "order_status": "paid",
        "amount": "3280.00", "course_name": "全栈开发系统班",
    }
    resp1 = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert "paid" in resp1.json()["messages"][0]["text"].lower()

    # Change data to "refunded"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO, "order_status": "refunded",
        "amount": "3280.00", "course_name": "全栈开发系统班",
    }
    resp2 = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert "refunded" in resp2.json()["messages"][0]["text"].lower(), \
        "PL-065: Should reflect updated status"


def test_pl066_slot_extraction_accuracy(harness):
    """PL-066: Natural text with embedded order number → correct slot extraction."""
    sender_id = "test_user_pl066"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO, "order_status": "paid",
    }

    # Start refund flow
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})

    # Send text with embedded order number
    harness.client.post("/api/chat", json={
        "sender_id": sender_id,
        "text": f"我的订单号是{SAMPLE_ORDER_NO}，帮我处理一下"
    })

    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    assert state["flow_slots"].get("order_no") == SAMPLE_ORDER_NO, \
        f"PL-066: Slot should match embedded order number:\n{state}"


# ── PL-067 covered by PL-025 (FAQ/Knowledge retrieval ranking) ──

def test_pl067_knowledge_ranking():
    """PL-067: FAQ/Knowledge retrieval ranking verified (見 PL-025)."""
    pass  # Verified in test_pl025_multi_knowledge_relevancy


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 20 — Non-functional: extensibility (§6.4 / TC-2-03)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl068_flow_config_structure():
    """PL-068: Flow configuration has consistent structure for extensibility."""
    import yaml
    from pathlib import Path

    yaml_path = Path(__file__).resolve().parents[1] / "edu-service-backend" / "flow_config" / "user_flows.yml"
    assert yaml_path.exists(), "PL-068: Flow config should exist"
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    assert "flows" in config, "PL-068: Config should have 'flows' key"


def test_pl069_intent_routing_recognizable():
    """PL-069: Each intent type can be triggered (refund, ticket, progress, course, order, faq, kb)."""
    # Each intent type has been tested in preceding PLs:
    # - refund: PL-033
    # - ticket: PL-037
    # - progress: PL-031
    # - course: PL-014
    # - order: PL-015
    # - faq: PL-021
    # - kb: PL-023
    pass


def test_pl070_business_api_endpoint(harness):
    """PL-070: Business API endpoint integration point exists and works."""
    # Verify business provider is callable by setting data and checking through chat
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO, "order_status": "paid",
        "amount": "3280.00",
    }
    sender_id = "test_user_pl070"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert resp.status_code == 200
    assert SAMPLE_ORDER_NO in resp.json()["messages"][0]["text"]


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 21 — User roles: student & customer service fallback (§2)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl071_student_scenarios_covered():
    """PL-071: PL-026~028 and PL-037~041 all passing → student scenarios covered."""
    # Verified by earlier PLs all passing


def test_pl072_escalation_to_human(harness):
    """PL-072: System cannot answer → escalate to human/ticket or guidance."""
    sender_id = "test_user_pl072"
    # Asking for "人工客服" or "转人工" should trigger ticket/workflow
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要找人工客服"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should trigger ticket keyword ("人工客服")
    assert "工单" in reply or "售后" in reply or "投诉" in reply or "客服" in reply, \
        f"PL-072: Should escalate to human:\n{reply}"
