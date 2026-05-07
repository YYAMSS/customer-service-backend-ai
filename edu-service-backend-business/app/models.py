from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Series(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int]
    delivery_mode: Mapped[str] = mapped_column(String(32))
    series_code: Mapped[str] = mapped_column(String(64))
    series_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_learner_identity_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_learning_goal_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    target_grade_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sale_status: Mapped[str] = mapped_column(String(32))
    created_by: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class SeriesCohort(Base):
    __tablename__ = "series_cohort"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int]
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id"))
    campus_id: Mapped[int | None] = mapped_column(nullable=True)
    head_teacher_id: Mapped[int]
    cohort_code: Mapped[str] = mapped_column(String(64))
    cohort_name: Mapped[str] = mapped_column(String(128))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    max_student_count: Mapped[int]
    current_student_count: Mapped[int]
    yn: Mapped[int]
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int]
    order_no: Mapped[str] = mapped_column(String(64))
    order_status: Mapped[str] = mapped_column(String(32))
    status_desc: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

