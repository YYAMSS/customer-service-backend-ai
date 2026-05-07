from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.app import app


EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("GET", "/students/{student_id}/courses"),
    ("GET", "/students/{student_id}/cohorts"),
    ("GET", "/students/{student_id}/orders"),
    ("GET", "/courses/{series_code}"),
    ("GET", "/cohorts/{cohort_code}"),
    ("GET", "/orders/{order_no}"),
}


def main() -> None:
    actual_routes = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    missing = sorted(EXPECTED_ROUTES - actual_routes)
    if missing:
        raise SystemExit(f"Missing business backend routes: {missing}")
    print("Business backend route smoke passed.")


if __name__ == "__main__":
    main()
