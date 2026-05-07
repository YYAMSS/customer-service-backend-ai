from __future__ import annotations

from fastapi import FastAPI

from app.api import router


openapi_tags = [
    {"name": "系统", "description": "服务可用性与基础检查接口。"},
    {"name": "学员", "description": "查询学员相关的课程/班次/订单列表。"},
    {"name": "课程", "description": "课程（series）相关查询接口。"},
    {"name": "班次", "description": "班次（series_cohort）相关查询接口。"},
    {"name": "订单", "description": "订单相关查询接口。"},
]


app = FastAPI(
    title="Education 业务服务",
    version="0.1.0",
    description="为教育智能客服项目提供课程、班次、订单等业务事实的示例服务。",
    openapi_tags=openapi_tags,
)

app.include_router(router)

