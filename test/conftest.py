"""Test configuration and shared fixtures for pipeline tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

# Set env vars BEFORE importing any atguigu_edu modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["BUSINESS_BASE_URL"] = "http://127.0.0.1:9999"
os.environ["LLM_API_KEY"] = "test-key"

# Inject a mock LLM module before atguigu_edu can import the real one.
# The orchestrator does `from atguigu_edu.infrastructure.llm import llm`,
# so we pre-populate sys.modules with a fake module whose `llm` attr always fails.
_fake_llm_module = type(sys)("atguigu_edu.infrastructure.llm")
_mock_llm = AsyncMock()
_mock_llm.ainvoke.side_effect = RuntimeError("LLM unavailable in test")
_fake_llm_module.llm = _mock_llm
_fake_llm_module.__spec__ = None
sys.modules["atguigu_edu.infrastructure.llm"] = _fake_llm_module

# Add edu-service-backend to path so tests can import from it
EDU_BACKEND = Path(__file__).resolve().parents[1] / "edu-service-backend"
if str(EDU_BACKEND) not in sys.path:
    sys.path.insert(0, str(EDU_BACKEND))

BUSINESS_BACKEND = Path(__file__).resolve().parents[1] / "edu-service-backend-business"
if str(BUSINESS_BACKEND) not in sys.path:
    sys.path.insert(0, str(BUSINESS_BACKEND))


class MockBusinessProvider:
    """A mock BusinessProvider that can be programmed with test data."""

    def __init__(self, order_data=None, course_data=None, cohort_data=None,
                 progress_data=None, courses_list=None, orders_list=None,
                 cohorts_list=None, health_data=None):
        self.order_data = order_data
        self.course_data = course_data
        self.cohort_data = cohort_data
        self.progress_data = progress_data
        self.courses_list = courses_list or []
        self.orders_list = orders_list or []
        self.cohorts_list = cohorts_list or []
        self.health_data = health_data or {"code": 0, "data": {"status": "ok"}}

    async def health(self) -> Any:
        return self.health_data.get("data")

    async def student_courses(self, student_id: str, limit: int = 10) -> Any:
        return {"courses": self.courses_list}

    async def student_cohorts(self, student_id: str, limit: int = 10) -> Any:
        return {"cohorts": self.cohorts_list}

    async def student_orders(self, student_id: str, limit: int = 10) -> Any:
        return {"orders": self.orders_list}

    async def course(self, series_code: str) -> Any:
        return self.course_data

    async def cohort(self, cohort_code: str) -> Any:
        return self.cohort_data

    async def order(self, order_no: str) -> Any:
        return self.order_data

    async def cohort_learning_progress(self, student_id: str, cohort_code: str) -> Any:
        return self.progress_data


class TestHarness:
    """Holds a TestClient and MockBusinessProvider, managing the app lifecycle."""

    def __init__(self, mock_business: MockBusinessProvider):
        self.mock_business = mock_business
        from atguigu_edu.api.app import app as _app
        from atguigu_edu.api.dependencies import get_business_provider

        async def _override_business_provider():
            yield mock_business

        _app.dependency_overrides[get_business_provider] = _override_business_provider
        self._app = _app
        self._client_context = TestClient(_app)
        # Enter the context manager to trigger lifespan startup
        self._client = self._client_context.__enter__()

    @property
    def client(self):
        return self._client

    def close(self):
        self._client_context.__exit__(None, None, None)


@pytest.fixture
def harness():
    """Create a TestHarness with a mock BusinessProvider.

    Tests can set data on harness.mock_business before making requests.
    """
    mock_bp = MockBusinessProvider()
    h = TestHarness(mock_bp)
    try:
        yield h
    finally:
        h.close()


@pytest.fixture
def sender_id_factory():
    """Generate unique sender_ids for test isolation."""
    import uuid
    def _make():
        return f"test_{uuid.uuid4().hex[:12]}"
    return _make


@pytest.fixture
def sample_order_data():
    """Default sample order data for mock BusinessProvider."""
    from test.pipeline_sample_data import SAMPLE_ORDER_NO, SAMPLE_COURSE_DISPLAY_NAME
    return {
        "order_no": SAMPLE_ORDER_NO,
        "course_name": SAMPLE_COURSE_DISPLAY_NAME,
        "status": "paid",
        "amount": "3280.00",
        "paid_at": "2024-04-01T10:30:00",
        "student_id": "student_pipeline_demo",
    }


@pytest.fixture
def sample_course_data():
    """Default sample course data for mock BusinessProvider."""
    from test.pipeline_sample_data import SAMPLE_SERIES_CODE, SAMPLE_COURSE_DISPLAY_NAME
    return {
        "series_code": SAMPLE_SERIES_CODE,
        "series_name": SAMPLE_COURSE_DISPLAY_NAME,
        "description": "全栈开发系统班 - 涵盖前端、后端、数据库，零基础到就业",
        "price": "3280.00",
        "original_price": "4580.00",
        "delivery_mode": "线上直播 + 线下面授",
        "target_audience": "在校学生、职场人士、求职者",
        "modules": [
            {"name": "前端开发基础", "hours": 60},
            {"name": "后端开发实战", "hours": 80},
            {"name": "数据库与部署", "hours": 40},
        ],
    }


@pytest.fixture
def sample_cohort_data():
    """Default sample cohort data for mock BusinessProvider."""
    from test.pipeline_sample_data import SAMPLE_COHORT_CODE, SAMPLE_COHORT_DISPLAY_NAME
    return {
        "cohort_code": SAMPLE_COHORT_CODE,
        "cohort_name": SAMPLE_COHORT_DISPLAY_NAME,
        "series_code": "fullstack_development_foundation",
        "series_name": "全栈开发系统班",
        "start_date": "2024-03-01",
        "status": "in_progress",
    }


@pytest.fixture
def sample_progress_data():
    """Default sample learning progress data for mock BusinessProvider."""
    return {
        "student_id": "student_pipeline_demo",
        "cohort_code": "C_fullstack_development_foundation",
        "attendance_rate": 0.85,
        "video_completion_rate": 0.72,
        "homework_completion_rate": 0.68,
        "exam_avg_score": 82.5,
    }
