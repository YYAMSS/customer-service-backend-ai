from __future__ import annotations

from typing import Any

from atguigu_edu.infrastructure.business_client import BusinessServiceClient


class BusinessProviderError(RuntimeError):
    pass


class BusinessProvider:
    def __init__(self, client: BusinessServiceClient) -> None:
        self._client = client

    @staticmethod
    def _unwrap(envelope: dict[str, Any]) -> Any:
        code = envelope.get("code", 0)
        if code != 0:
            raise BusinessProviderError(envelope.get("message", "business service error"))
        return envelope.get("data")

    async def health(self) -> Any:
        return self._unwrap(await self._client.health())

    async def student_courses(self, student_id: str, limit: int = 10) -> Any:
        return self._unwrap(await self._client.get_student_courses(student_id=student_id, limit=limit))

    async def student_cohorts(self, student_id: str, limit: int = 10) -> Any:
        return self._unwrap(await self._client.get_student_cohorts(student_id=student_id, limit=limit))

    async def student_orders(self, student_id: str, limit: int = 10) -> Any:
        return self._unwrap(await self._client.get_student_orders(student_id=student_id, limit=limit))

    async def course(self, series_code: str) -> Any:
        return self._unwrap(await self._client.get_course(series_code=series_code))

    async def cohort(self, cohort_code: str) -> Any:
        return self._unwrap(await self._client.get_cohort(cohort_code=cohort_code))

    async def order(self, order_no: str) -> Any:
        return self._unwrap(await self._client.get_order(order_no=order_no))

