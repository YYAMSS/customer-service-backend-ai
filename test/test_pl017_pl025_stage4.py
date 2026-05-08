"""Stage 4 tests: Information retrieval (PL-017 through PL-025)."""
from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COHORT_CODE, SAMPLE_COURSE_DISPLAY_NAME, SAMPLE_SERIES_CODE


# ── PL-017 ──────────────────────────────────────────────────────────────────

def test_pl017_course_info_retrieval(harness):
    """Query real course info returns course name or consistent fields."""
    sender_id = "test_user_pl017"
    harness.mock_business.courses_list = [
        {"series_code": SAMPLE_SERIES_CODE, "series_name": SAMPLE_COURSE_DISPLAY_NAME}
    ]
    harness.mock_business.course_data = {
        "series_code": SAMPLE_SERIES_CODE,
        "series_name": SAMPLE_COURSE_DISPLAY_NAME,
        "description": "全栈开发系统班 - 涵盖前端、后端、数据库",
        "target_audience": "在校学生、职场人士",
        "delivery_mode": "线上直播 + 线下面授",
        "sale_status": "在售",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id,
        "text": "全栈开发系统班是什么课程"
    })
    assert resp.status_code == 200
    body = resp.json()
    reply = body["messages"][0]["text"]
    assert SAMPLE_COURSE_DISPLAY_NAME in reply or "全栈" in reply


# ── PL-018 ──────────────────────────────────────────────────────────────────

def test_pl018_cohort_info_retrieval(harness):
    """Query cohort schedule returns info consistent with sample data."""
    sender_id = "test_user_pl018"
    harness.mock_business.courses_list = [
        {"series_code": SAMPLE_SERIES_CODE, "series_name": SAMPLE_COURSE_DISPLAY_NAME}
    ]
    harness.mock_business.course_data = {
        "series_code": SAMPLE_SERIES_CODE,
        "series_name": SAMPLE_COURSE_DISPLAY_NAME,
        "target_audience": "在校学生、职场人士",
        "delivery_mode": "线上直播 + 线下面授",
        "sale_status": "在售",
    }
    harness.mock_business.cohort_data = {
        "cohort_code": SAMPLE_COHORT_CODE,
        "cohort_name": "全栈开发系统班 · 默认班",
        "start_date": "2024-03-01",
        "status": "in_progress",
    }
    harness.mock_business.cohorts_list = [
        {"cohort_code": SAMPLE_COHORT_CODE, "cohort_name": "全栈开发系统班 · 默认班"}
    ]

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id,
        "text": f"查询班次 {SAMPLE_COHORT_CODE} 的开课安排"
    })
    assert resp.status_code == 200
    body = resp.json()
    reply = body["messages"][0]["text"]
    # Should contain cohort info or acknowledge unknown
    assert any(w in reply for w in [SAMPLE_COHORT_CODE, "全栈", "班次", "开课", "课程"]), \
        f"Reply should reference cohort info:\n{reply}"


# ── PL-019 ──────────────────────────────────────────────────────────────────

def test_pl019_order_detail_retrieval(harness):
    """Order dimension query returns status/amount consistent with data."""
    sender_id = "test_user_pl019"
    harness.mock_business.order_data = {
        "order_no": SAMPLE_ORDER_NO,
        "order_status": "paid",
        "amount": "3280.00",
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
        "paid_at": "2024-04-01T10:30:00",
        "created_at": "2024-03-28T09:00:00",
    }

    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id,
        "text": f"查询订单 {SAMPLE_ORDER_NO}"
    })
    assert resp.status_code == 200
    body = resp.json()
    reply = body["messages"][0]["text"]
    assert SAMPLE_ORDER_NO in reply
    assert "3280" in reply, f"Reply should contain amount:\n{reply}"


# ── PL-020 ──────────────────────────────────────────────────────────────────

def test_pl020_learning_record_retrieval(harness):
    """Query learning records returns structured data or natural language with data dimensions."""
    sender_id = "test_user_pl020"
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
    body = resp.json()
    reply = body["messages"][0]["text"]
    # Should contain at least one progress dimension
    assert any(w in reply for w in ["出勤", "考勤", "视频", "作业", "考试", "85", "72", "68", "82"]), \
        f"Reply should have progress data:\n{reply}"


# ── PL-021 ──────────────────────────────────────────────────────────────────

def test_pl021_faq_refund_policy(harness):
    """FAQ query about refund policy returns matching canned response."""
    sender_id = "test_user_pl021"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "退款政策是什么"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "退款" in reply and "开课" in reply


# ── PL-022 ──────────────────────────────────────────────────────────────────

def test_pl022_faq_enrollment_policy(harness):
    """FAQ query about enrollment/start policy returns matching response."""
    sender_id = "test_user_pl022"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "开课政策和时间"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "开课" in reply, f"Reply should mention enrollment:\n{reply}"


# ── PL-023 ──────────────────────────────────────────────────────────────────

def test_pl023_platform_rules_knowledge(harness):
    """Query about platform rules returns knowledge base response."""
    sender_id = "test_user_pl023"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "平台规则和违规处理"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "知识库" in reply or "平台规则" in reply, f"Reply should reference knowledge:\n{reply}"


# ── PL-024 ──────────────────────────────────────────────────────────────────

def test_pl024_usage_guide_knowledge(harness):
    """Query about usage guide returns knowledge base response."""
    sender_id = "test_user_pl024"
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "怎么使用这个平台"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    assert "知识库" in reply or "使用指南" in reply or "选课" in reply, \
        f"Reply should have usage guide:\n{reply}"


# ── PL-025 ──────────────────────────────────────────────────────────────────

def test_pl025_multi_knowledge_relevancy(harness):
    """When multiple matching knowledge items exist, top result should be relevant."""
    sender_id = "test_user_pl025"
    # "退款相关的政策" should trigger FAQ refund reply, not a generic chitchat
    resp = harness.client.post("/api/chat", json={
        "sender_id": sender_id, "text": "能退款吗"
    })
    assert resp.status_code == 200
    reply = resp.json()["messages"][0]["text"]
    # Should get a relevant FAQ response, not chitchat
    assert "退款" in reply, f"Should get relevant refund info, not chitchat:\n{reply}"
    # Should not be the generic chitchat
    assert "我是教育智能客服" not in reply, f"Should not fall back to generic chitchat:\n{reply}"
