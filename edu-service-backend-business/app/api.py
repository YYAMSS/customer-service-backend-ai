from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ApiResponse,
    CohortSummaryData,
    CourseSummaryData,
    LearningProgressData,
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


@router.get(
    "/students/{student_id}/cohorts/{cohort_code}/learning-progress",
    response_model=ApiResponse,
    tags=["学员"],
    summary="查询学员在某班次的学习进度汇总（演示）",
    description=(
        "聚合考勤、课次规模；作业/考试若无明细数据则返回 0。"
        "当前 demo 数据库中学员与前台 sender_id 未必一致，优先返回班次内一名示例学员的考勤。"
    ),
)
def learning_progress(student_id: str, cohort_code: str, db: Session = Depends(get_db)):
    cohort_row = db.execute(
        text(
            """
            SELECT c.id AS cohort_id, c.cohort_code, c.cohort_name, s.series_code
            FROM series_cohort c
            JOIN series s ON s.id = c.series_id
            WHERE c.cohort_code = :cohort_code
            LIMIT 1
            """
        ),
        {"cohort_code": cohort_code},
    ).mappings().first()
    if not cohort_row:
        raise HTTPException(status_code=404, detail=f"班次 {cohort_code} 不存在。")

    cohort_id = int(cohort_row["cohort_id"])
    scheduled_sessions = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM series_cohort_session scs
                INNER JOIN series_cohort_course scco ON scs.series_cohort_course_id = scco.id
                WHERE scco.cohort_id = :cid
                """
            ),
            {"cid": cohort_id},
        ).scalar()
        or 0
    )

    sid_row = db.execute(
        text(
            """
            SELECT student_id
            FROM student_cohort_rel
            WHERE cohort_id = :cid
            LIMIT 1
            """
        ),
        {"cid": cohort_id},
    ).first()
    db_student_id = int(sid_row[0]) if sid_row else None

    present = absent = att_rows = 0
    if db_student_id is not None:
        agg = db.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(CASE WHEN attendance_status IN ('present', 'late') THEN 1 ELSE 0 END), 0)
                    AS present_cnt,
                  COALESCE(SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END), 0)
                    AS absent_cnt,
                  COALESCE(COUNT(*), 0) AS row_cnt
                FROM session_attendance
                WHERE cohort_id = :cid AND student_id = :sid
                """
            ),
            {"cid": cohort_id, "sid": db_student_id},
        ).first()
        if agg:
            present, absent, att_rows = int(agg[0]), int(agg[1]), int(agg[2])

    denom = max(scheduled_sessions, att_rows)
    hw_total = int(
        db.execute(
            text(
                """
                SELECT COUNT(DISTINCT sh.id)
                FROM session_homework sh
                INNER JOIN series_cohort_session scs ON sh.session_id = scs.id
                INNER JOIN series_cohort_course scco ON scs.series_cohort_course_id = scco.id
                WHERE scco.cohort_id = :cid
                """
            ),
            {"cid": cohort_id},
        ).scalar()
        or 0
    )
    hw_done = 0
    if db_student_id is not None and hw_total:
        hw_done = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM session_homework_submission hsub
                    INNER JOIN session_homework sh ON hsub.homework_id = sh.id
                    INNER JOIN series_cohort_session scs ON sh.session_id = scs.id
                    INNER JOIN series_cohort_course scco ON scs.series_cohort_course_id = scco.id
                    WHERE scco.cohort_id = :cid AND hsub.student_id = :sid
                    """
                ),
                {"cid": cohort_id, "sid": db_student_id},
            ).scalar()
            or 0
        )

    exam_total = int(
        db.execute(
            text(
                """
                SELECT COUNT(DISTINCT se.id)
                FROM session_exam se
                INNER JOIN series_cohort_session scs ON se.session_id = scs.id
                INNER JOIN series_cohort_course scco ON scs.series_cohort_course_id = scco.id
                WHERE scco.cohort_id = :cid
                """
            ),
            {"cid": cohort_id},
        ).scalar()
        or 0
    )
    exam_done = 0
    if db_student_id is not None and exam_total:
        exam_done = int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM session_exam_submission esub
                    INNER JOIN session_exam se ON esub.exam_id = se.id
                    INNER JOIN series_cohort_session scs ON se.session_id = scs.id
                    INNER JOIN series_cohort_course scco ON scs.series_cohort_course_id = scco.id
                    WHERE scco.cohort_id = :cid AND esub.student_id = :sid
                    """
                ),
                {"cid": cohort_id, "sid": db_student_id},
            ).scalar()
            or 0
        )

    video_total = denom
    video_done = min(present, video_total) if video_total else 0

    note = ""
    if db_student_id is None:
        note = "数据库中暂无该班次的学员报名记录，考勤/作业/考试为占位统计。"
    elif scheduled_sessions == 0:
        note = "该班次尚未配置课次，进度分母可能为 0。"

    return _wrap(
        LearningProgressData(
            student_id=student_id,
            cohort_code=str(cohort_row.get("cohort_code") or ""),
            cohort_name=str(cohort_row.get("cohort_name") or ""),
            series_code=str(cohort_row.get("series_code") or ""),
            attendance_present=present,
            attendance_absent=absent,
            attendance_scheduled=denom,
            video_completed=video_done,
            video_total=video_total,
            homework_submitted=hw_done,
            homework_total=hw_total,
            exam_taken=exam_done,
            exam_total=exam_total,
            note=note,
        )
    )

