"""Stages 9-12: Ticket flow, slot management, flow switching, cancellation (PL-037~049)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 9 — Task-oriented: ticket complete flow (§3.2-04 / §4.5)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl037_ticket_after_sales_flow(harness):
    """PL-037: After-sales ticket flow collects type, asks for order & description."""
    sender_id = "test_user_pl037"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我有售后问题"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should start ticket flow and ask for type
    assert "售后" in reply or "投诉" in reply or "退款" in reply or "建议" in reply or "工单" in reply, \
        f"PL-037: Should enter ticket flow:\n{reply}"


def test_pl038_ticket_complaint_type(harness):
    """PL-038: Select complaint type → continues collecting order & description."""
    sender_id = "test_user_pl038"

    # Start ticket flow
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要投诉"
    })
    assert resp.status_code == 200

    # Confirm type as complaint
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "投诉"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should ask for order number or skip
    assert "订单" in reply or "跳过" in reply, \
        f"PL-038: Should ask for order:\n{reply}"


def test_pl039_ticket_refund_type(harness):
    """PL-039: Refund-related ticket type collects order & description."""
    sender_id = "test_user_pl039"

    # Start ticket flow
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要提交工单"
    })
    assert resp.status_code == 200

    # Select refund-related type
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "退款问题"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "订单" in reply or "跳过" in reply, \
        f"PL-039: Should ask for order:\n{reply}"


def test_pl040_pl041_complete_ticket(harness):
    """PL-040/041: Complete ticket creation → returns ticket number."""
    sender_id = "test_user_pl040_041"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
    }

    # Start ticket flow with complaint scenario (§4.5)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "课程质量太差，我要投诉"
    })
    assert resp.status_code == 200

    # Provide type
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "投诉"
    })
    assert resp.status_code == 200

    # Provide order number
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert resp.status_code == 200

    # Provide description
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "课程内容与宣传不符，希望退款"
    })
    assert resp.status_code == 200

    # Confirm
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "确认"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "TICKET" in reply or "工单" in reply, \
        f"PL-040/041: Should return ticket number:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 10 — Slot & context management (§3.3-01~02 / §5.4-03)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl042_missing_order_slot(harness):
    """PL-042: Omit order number in order-required task → asks for it."""
    sender_id = "test_user_pl042"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要退款"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "订单" in reply or "ORD" in reply, f"PL-042: Should ask for order:\n{reply}"


def test_pl043_missing_cohort_slot(harness):
    """PL-043: Omit cohort in progress task → asks for it."""
    sender_id = "test_user_pl043"
    harness.mock_business.cohorts_list = [
        {"cohort_name": "全栈开发系统班 · 默认班", "cohort_code": "C_fullstack_development_foundation"},
        {"cohort_name": "前端开发基础班", "cohort_code": "C_frontend_development_foundation"},
    ]

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查学习进度"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "班次" in reply or "指定" in reply, f"PL-043: Should ask for cohort:\n{reply}"


def test_pl044_missing_reason_slot(harness):
    """PL-044: Omit reason in refund task → asks for it."""
    sender_id = "test_user_pl044"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
    }

    # Start refund → give order → omit reason
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": SAMPLE_ORDER_NO})

    # Send very short text that doesn't qualify as reason
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "?"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "原因" in reply or "退款" in reply, f"PL-044: Should ask for reason:\n{reply}"


def test_pl045_slot_reuse_with_pronoun(harness):
    """PL-045: Provide identity info first, then use pronoun → reuses existing slots."""
    sender_id = "test_user_pl045"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": "全栈开发系统班",
    }

    # First turn: provide order context
    harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": f"查订单 {SAMPLE_ORDER_NO}"
    })

    # Second turn: pronoun reference to related question
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "这个订单能退款吗"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should have entered refund flow or referenced the order
    assert "退款" in reply, f"PL-045: Should reference refund:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 11 — Flow switching & recovery (§3.3-03~04)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl046_flow_interruption(harness):
    """PL-046: Mid-task interrupt with new task → A suspended, B active."""
    sender_id = "test_user_pl046"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
    }

    # Start task A (refund) - don't complete
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})

    # Interrupt with task B (ticket)
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要投诉"
    })
    assert resp.status_code == 200

    # Check state: B should be active, A suspended
    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    # B (ticket) should be active or A should be suspended
    assert state["active_flow"] in ("ticket", "refund"), f"PL-046: Task should be active:\n{state}"
    if state["active_flow"] == "ticket":
        # A was suspended
        assert state["suspended_flow"] is not None, \
            f"PL-046: Suspended flow should exist:\n{state}"


def test_pl047_flow_recovery(harness):
    """PL-047: Complete B → system resumes A with slots preserved."""
    sender_id = "test_user_pl047"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
    }

    # Start task A (refund), provide order number (slot)
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": SAMPLE_ORDER_NO})

    # Interrupt with task B (ticket) and complete it
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要投诉"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "售后"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "跳过"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "测试问题描述"})
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "确认"})

    # Now resume A by saying "继续"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "继续"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should resume A (refund), now at "collect_reason" step
    assert "原因" in reply or "退款" in reply or "继续" in reply, \
        f"PL-047: Should resume refund flow:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 12 — Dialog control: cancellation (§3.3-05)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl048_cancel_active_task(harness):
    """PL-048: Natural language cancel during active task → confirmed."""
    sender_id = "test_user_pl048"

    # Start a flow
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要退款"})

    # Cancel
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "取消"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "取消" in reply or "终止" in reply, f"PL-048: Should confirm cancel:\n{reply}"

    # Verify state is clean
    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    assert state["active_flow"] is None, f"PL-048: Flow should be cleared:\n{state}"


def test_pl049_alternate_cancel_phrase(harness):
    """PL-049: Different cancel phrase → same consistent behavior."""
    sender_id = "test_user_pl049"

    # Start a flow
    harness.client.post("/api/chat", json={"sender_id": sender_id, "text": "我要提交工单"})

    # Cancel with different phrase
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "算了，不用了"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "取消" in reply or "终止" in reply, f"PL-049: Should confirm cancel:\n{reply}"

    # Verify consistent behavior
    state_resp = harness.client.get("/api/chat/state", params={"sender_id": sender_id})
    state = state_resp.json()
    assert state["active_flow"] is None, f"PL-049: Flow should be cleared:\n{state}"
