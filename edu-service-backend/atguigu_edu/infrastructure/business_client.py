from __future__ import annotations

from typing import Any

import httpx


class BusinessServiceClient:
    def __init__(self, base_url: str, timeout_s: float = 5.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_s),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health(self) -> dict[str, Any]:
        resp = await self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    async def get_student_courses(self, student_id: str, limit: int = 10) -> dict[str, Any]:
        resp = await self._client.get(f"/students/{student_id}/courses", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()

    async def get_course(self, series_code: str) -> dict[str, Any]:
        resp = await self._client.get(f"/courses/{series_code}")
        resp.raise_for_status()
        return resp.json()

    async def get_student_cohorts(self, student_id: str, limit: int = 10) -> dict[str, Any]:
        resp = await self._client.get(f"/students/{student_id}/cohorts", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()

    async def get_cohort(self, cohort_code: str) -> dict[str, Any]:
        resp = await self._client.get(f"/cohorts/{cohort_code}")
        resp.raise_for_status()
        return resp.json()

    async def get_student_orders(self, student_id: str, limit: int = 10) -> dict[str, Any]:
        resp = await self._client.get(f"/students/{student_id}/orders", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()

    async def get_order(self, order_no: str) -> dict[str, Any]:
        resp = await self._client.get(f"/orders/{order_no}")
        resp.raise_for_status()
        return resp.json()

