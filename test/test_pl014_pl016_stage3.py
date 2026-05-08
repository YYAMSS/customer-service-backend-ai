"""Stage 3 tests: Intent classification & Q&A (PL-014 through PL-016)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COHORT_CODE, SAMPLE_COURSE_DISPLAY_NAME, SAMPLE_SERIES_CODE


# ── PL-014 ──────────────────────────────────────────────────────────────────

def test_pl014_course_consultation_intent(harness):
    """Explicit course consultation triggers consultation intent with non-empty reply."""
    sender_id = "test_user_pl014"

    # Provide mock course data
    harness.mock_business.courses_list = [
        {
            "series_code": SAMPLE_SERIES_CODE,
            "series_name": SAMPLE_COURSE_DISPLAY_NAME,
            "delivery_mode": "线上直播",
            "sale_status": "on_sale",
        }
    ]
    harness.mock_business.course_data = {
        "series_code": SAMPLE_SERIES_CODE,
        "series_name": SAMPLE_COURSE_DISPLAY_NAME,
        "description": "全栈开发系统班",
        "target_audience": "在校学生、职场人士、求职者",
        "delivery_mode": "线上直播 + 线下面授",
        "sale_status": "在售",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "我想咨询全栈开发课程"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) >= 1
    reply = body["messages"][0]["text"]
    assert reply, "Reply should not be empty"
    # Should reference the course name
    assert SAMPLE_COURSE_DISPLAY_NAME in reply or "全栈" in reply or "课程" in reply


# ── PL-015 ──────────────────────────────────────────────────────────────────

def test_pl015_order_query_intent(harness):
    """Order query with order number triggers order intent, reply contains order info."""
    sender_id = "test_user_pl015"

    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
        "paid_at": "2024-04-01T10:30:00",
        "created_at": "2024-03-28T09:00:00",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": f"帮我查一下订单 {SAMPLE_ORDER_NO}"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) >= 1
    reply = body["messages"][0]["text"]
    assert SAMPLE_ORDER_NO in reply, f"Reply should contain order number:\n{reply}"
    # Should contain at least order status or payment info
    assert "paid" in reply.lower() or "状态" in reply or "3280" in reply, \
        f"Reply should contain order status or amount:\n{reply}"


# ── PL-016 ──────────────────────────────────────────────────────────────────

def test_pl016_learning_progress_intent(harness):
    """Learning progress query triggers progress intent with progress-related info."""
    sender_id = "test_user_pl016"

    # Provide mock cohort data (single cohort so it queries directly)
    harness.mock_business.cohorts_list = [
        {"cohort_name": "全栈开发系统班 · 默认班", "cohort_code": SAMPLE_COHORT_CODE},
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
        "text": f"我在这{SAMPLE_COHORT_CODE}班学了什么，查学习进度"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) >= 1
    reply = body["messages"][0]["text"]
    assert reply, "Reply should not be empty"
    # Should contain some progress-related info
    assert any(w in reply for w in ["进度", "出勤", "考勤", "视频", "作业", "考试", "班次"]), \
        f"Reply should contain progress information:\n{reply}"
