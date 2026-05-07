from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ApiResponse,
    CohortSummaryData,
    CourseSummaryData,
    OrderSummaryData,
    StudentCohortsData,
    StudentCoursesData,
    StudentOrdersData,
)


router = APIRouter()


def _wrap(data):
    return ApiResponse(data=data)


@router.get(
    "/health",
    response_model=ApiResponse,
    tags=["系统"],
    summary="健康检查",
    description="用于检查服务和数据库连接是否正常。",
)
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return _wrap({"status": "ok"})


@router.get(
    "/students/{student_id}/courses",
    response_model=ApiResponse,
    tags=["学员"],
    summary="查询学员可见课程列表",
    description="返回课程（series）列表，用于前端展示课程对象列表。当前为 demo：不按学员过滤。",
)
def student_courses(student_id: str, limit: int = 10, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT series_code, series_name, sale_status, delivery_mode
            FROM series
            ORDER BY updated_at DESC, id DESC
            LIMIT :limit
            """
        )
        , {"limit": max(1, min(int(limit), 50))}
    ).mappings().all()

    courses = [
        CourseSummaryData(
            series_code=str(r.get("series_code") or ""),
            series_name=str(r.get("series_name") or ""),
            sale_status=str(r.get("sale_status") or ""),
            delivery_mode=str(r.get("delivery_mode") or ""),
        )
        for r in rows
    ]
    return _wrap(StudentCoursesData(student_id=student_id, courses=courses))


@router.get(
    "/courses/{series_code}",
    response_model=ApiResponse,
    tags=["课程"],
    summary="查询课程详情（按 series_code）",
    description="返回指定课程的基础信息。当前仅返回 summary 字段。",
)
def course_detail(series_code: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT series_code, series_name, sale_status, delivery_mode
            FROM series
            WHERE series_code = :series_code
            LIMIT 1
            """
        ),
        {"series_code": series_code},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"课程 {series_code} 不存在。")
    return _wrap(
        CourseSummaryData(
            series_code=str(row.get("series_code") or ""),
            series_name=str(row.get("series_name") or ""),
            sale_status=str(row.get("sale_status") or ""),
            delivery_mode=str(row.get("delivery_mode") or ""),
        )
    )


@router.get(
    "/students/{student_id}/cohorts",
    response_model=ApiResponse,
    tags=["学员"],
    summary="查询学员可见班次列表",
    description="返回班次（series_cohort）列表，用于前端展示班次对象列表。当前为 demo：不按学员过滤。",
)
def student_cohorts(student_id: str, limit: int = 10, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT
              c.cohort_code,
              c.cohort_name,
              c.sale_price,
              c.start_date,
              c.end_date,
              s.series_code
            FROM series_cohort c
            JOIN series s ON s.id = c.series_id
            ORDER BY c.updated_at DESC, c.id DESC
            LIMIT :limit
            """
        )
        , {"limit": max(1, min(int(limit), 50))}
    ).mappings().all()

    cohorts = [
        CohortSummaryData(
            cohort_code=str(r.get("cohort_code") or ""),
            cohort_name=str(r.get("cohort_name") or ""),
            series_code=str(r.get("series_code") or ""),
            sale_price=r.get("sale_price"),
            start_date=r.get("start_date"),
            end_date=r.get("end_date"),
        )
        for r in rows
    ]
    return _wrap(StudentCohortsData(student_id=student_id, cohorts=cohorts))


@router.get(
    "/cohorts/{cohort_code}",
    response_model=ApiResponse,
    tags=["班次"],
    summary="查询班次详情（按 cohort_code）",
    description="返回指定班次的基础信息。当前仅返回 summary 字段。",
)
def cohort_detail(cohort_code: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT
              c.cohort_code,
              c.cohort_name,
              c.sale_price,
              c.start_date,
              c.end_date,
              s.series_code
            FROM series_cohort c
            JOIN series s ON s.id = c.series_id
            WHERE c.cohort_code = :cohort_code
            LIMIT 1
            """
        ),
        {"cohort_code": cohort_code},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"班次 {cohort_code} 不存在。")
    return _wrap(
        CohortSummaryData(
            cohort_code=str(row.get("cohort_code") or ""),
            cohort_name=str(row.get("cohort_name") or ""),
            series_code=str(row.get("series_code") or ""),
            sale_price=row.get("sale_price"),
            start_date=row.get("start_date"),
            end_date=row.get("end_date"),
        )
    )


@router.get(
    "/students/{student_id}/orders",
    response_model=ApiResponse,
    tags=["学员"],
    summary="查询学员订单列表",
    description="返回订单列表。当前为 demo：不按学员过滤，订单为空时返回空数组。",
)
def student_orders(student_id: str, limit: int = 10, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT order_no, order_status, payable_amount, created_at
            FROM `order`
            ORDER BY created_at DESC, id DESC
            LIMIT :limit
            """
        )
        , {"limit": max(1, min(int(limit), 50))}
    ).mappings().all()

    orders = [
        OrderSummaryData(
            order_no=str(r.get("order_no") or ""),
            order_status=str(r.get("order_status") or ""),
            status_desc=str(r.get("order_status") or ""),
            amount=r.get("payable_amount"),
            created_at=r.get("created_at"),
        )
        for r in rows
    ]
    return _wrap(StudentOrdersData(student_id=student_id, orders=orders))


@router.get(
    "/orders/{order_no}",
    response_model=ApiResponse,
    tags=["订单"],
    summary="查询订单详情（按 order_no）",
    description="返回指定订单的基础信息。当前仅返回 summary 字段。",
)
def order_detail(order_no: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT order_no, order_status, payable_amount, created_at
            FROM `order`
            WHERE order_no = :order_no
            LIMIT 1
            """
        ),
        {"order_no": order_no},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail=f"订单 {order_no} 不存在。")
    return _wrap(
        OrderSummaryData(
            order_no=str(row.get("order_no") or ""),
            order_status=str(row.get("order_status") or ""),
            status_desc=str(row.get("order_status") or ""),
            amount=row.get("payable_amount"),
            created_at=row.get("created_at"),
        )
    )

