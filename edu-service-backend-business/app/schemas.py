from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any


class CourseSummaryData(BaseModel):
    series_code: str
    series_name: str
    sale_status: str
    delivery_mode: str


class CohortSummaryData(BaseModel):
    cohort_code: str
    cohort_name: str
    series_code: str
    sale_price: Decimal
    start_date: date
    end_date: date | None = None


class OrderSummaryData(BaseModel):
    order_no: str
    order_status: str
    status_desc: str
    amount: Decimal
    created_at: datetime


class StudentCoursesData(BaseModel):
    student_id: str
    courses: list[CourseSummaryData]


class StudentCohortsData(BaseModel):
    student_id: str
    cohorts: list[CohortSummaryData]


class StudentOrdersData(BaseModel):
    student_id: str
    orders: list[OrderSummaryData]


class LearningProgressData(BaseModel):
    student_id: str
    cohort_code: str
    cohort_name: str
    series_code: str
    attendance_present: int
    attendance_absent: int
    attendance_scheduled: int
    video_completed: int
    video_total: int
    homework_submitted: int
    homework_total: int
    exam_taken: int
    exam_total: int
    note: str = ""

