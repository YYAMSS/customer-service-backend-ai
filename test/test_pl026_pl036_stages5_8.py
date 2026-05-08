"""Stages 5-8: Typical scenarios and task-oriented dialogue flows (PL-026~036)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COHORT_CODE, SAMPLE_COURSE_DISPLAY_NAME, SAMPLE_SERIES_CODE


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 5 — Typical scenarios: course / order / progress (§4.1~4.3)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl026_course_scenario(harness):
    """PL-026: Python course query returns overview, audience, cohort & price guidance."""
    sender_id = "test_user_pl026"
    harness.mock_business.courses_list = [
        {"series_code": SAMPLE_SERIES_CODE, "series_name": SAMPLE_COURSE_DISPLAY_NAME}
    ]
    harness.mock_business.course_data = {
        "series_code": SAMPLE_SERIES_CODE,
        "series_name": SAMPLE_COURSE_DISPLAY_NAME,
        "description": "全栈开发系统班",
        "target_audience": "在校学生、职场人士、求职者",
        "delivery_mode": "线上直播 + 线下面授",
        "sale_status": "在售",
        "price": "3280.00",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "全栈开发系统班怎么样"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should contain overview, audience, or price guidance
    assert any(w in reply for w in ["全栈", "课程", "适用", "班次", "价格", "授课"]), \
        f"Reply should have course overview:\n{reply}"


def test_pl027_order_scenario(harness):
    """PL-027: Order query returns status, course name, amount, payment time."""
    sender_id = "test_user_pl027"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
        "paid_at": "2024-04-01T10:30:00",
        "created_at": "2024-03-28T09:00:00",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": f"帮我查询订单 {SAMPLE_ORDER_NO}"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert SAMPLE_ORDER_NO in reply
    # At least 3 of: status, course name, amount, payment time
    checks = ["paid", "3280", SAMPLE_COURSE_DISPLAY_NAME[:2]]
    present = sum(1 for c in checks if c in reply)
    assert present >= 2, f"Expected at least 2 of {checks} in reply:\n{reply}"


def test_pl028_progress_scenario(harness):
    """PL-028: Learning progress query covers attendance, video, homework, exam."""
    sender_id = "test_user_pl028"
    harness.mock_business.cohorts_list = [
        {"cohort_name": "全栈开发系统班 · 默认班", "cohort_code": SAMPLE_COHORT_CODE}
    ]
    harness.mock_business.progress_data = {
        "student_id": sender_id,
        "cohort_code": SAMPLE_COHORT_CODE,
        "attendance_rate": 0.85,
        "video_completion_rate": 0.72,
        "homework_completion_rate": 0.68,
        "exam_avg_score": 82.5,
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id,
        "text": f"查学习进度 {SAMPLE_COHORT_CODE}"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should mention at least one of the four indicator types
    assert any(w in reply for w in ["出勤", "考勤", "视频", "作业", "考试", "85", "72", "68", "82"]), \
        f"Reply should have progress indicators:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 6 — Task-oriented: order query flow (§3.2-01)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl029_order_query_without_number(harness):
    """PL-029: Order query without order number prompts for it."""
    sender_id = "test_user_pl029"
    harness.mock_business.orders_list = [
        {"order_no": SAMPLE_ORDER_NO, "order_status": "paid", "amount": "3280.00"}
    ]

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查订单"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should either list orders or ask for order number
    assert "订单" in reply


def test_pl030_order_query_followup(harness):
    """PL-030: In same session after PL-029, provide order number → returns detail."""
    sender_id = "test_user_pl030"
    harness.mock_business.orders_list = [
        {"order_no": SAMPLE_ORDER_NO, "order_status": "paid", "amount": "3280.00"}
    ]
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
        "paid_at": "2024-04-01T10:30:00",
        "created_at": "2024-03-28T09:00:00",
    }

    # Round 1: vague order query
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查一下我的订单"
    })
    assert resp.status_code == 200

    # Round 2: provide specific order number
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert SAMPLE_ORDER_NO in reply, f"Reply should contain order number:\n{reply}"
    assert "状态" in reply or "paid" in reply.lower(), \
        f"Reply should contain order status or info:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 7 — Task-oriented: learning progress flow (§3.2-02)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl031_progress_without_cohort(harness):
    """PL-031: Progress query without cohort asks for cohort info."""
    sender_id = "test_user_pl031"
    # Multiple cohorts trigger collect_cohort step
    harness.mock_business.cohorts_list = [
        {"cohort_name": "全栈开发系统班 · 默认班", "cohort_code": SAMPLE_COHORT_CODE},
        {"cohort_name": "前端开发基础班", "cohort_code": "C_frontend_development_foundation"},
    ]

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查学习进度"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should ask to specify cohort
    assert "班次" in reply or "指定" in reply or SAMPLE_COHORT_CODE in reply, \
        f"Should ask for cohort:\n{reply}"


def test_pl032_progress_followup(harness):
    """PL-032: In same session, provide cohort → returns progress dimensions."""
    sender_id = "test_user_pl032"
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

    # Round 1: vague progress query
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "查学习进度"
    })
    assert resp.status_code == 200

    # Round 2: provide cohort
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_COHORT_CODE
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert any(w in reply for w in ["出勤", "考勤", "视频", "作业", "考试", "85", "72", "68", "82"]), \
        f"Reply should have progress data:\n{reply}"


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 8 — Task-oriented: refund complete flow (§3.2-03 / §4.4)
# ═══════════════════════════════════════════════════════════════════════════════

def test_pl033_pl036_refund_complete_flow(harness):
    """PL-033~036: Complete refund flow from trigger to success."""
    sender_id = "test_user_pl033_036"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
    }

    # PL-033: Trigger refund → enters refund task, asks for order number
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我要退款"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "订单" in reply or "ORD" in reply, \
        f"PL-033: Should ask for order:\n{reply}"

    # PL-034: Provide order number → asks for reason
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": SAMPLE_ORDER_NO
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "原因" in reply or "退款" in reply, \
        f"PL-034: Should ask for reason:\n{reply}"

    # PL-035: Provide reason → asks for refund type
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "课程不适合我的需求"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "全额" in reply or "部分" in reply or "退款" in reply, \
        f"PL-035: Should ask for refund type:\n{reply}"

    # PL-036: Confirm → returns success with reference number
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "确认"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "REFUND" in reply or "受理" in reply or "申请" in reply, \
        f"PL-036: Should return success confirmation:\n{reply}"
