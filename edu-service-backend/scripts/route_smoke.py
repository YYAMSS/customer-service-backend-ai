from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atguigu_edu.api.app import app


EXPECTED_ROUTES = {
    ("POST", "/api/chat"),
    ("GET", "/api/chat/history"),
}


def main() -> None:
    actual_routes = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    missing = sorted(EXPECTED_ROUTES - actual_routes)
    if missing:
        raise SystemExit(f"Missing dialogue backend routes: {missing}")
    print("Dialogue backend route smoke passed.")


if __name__ == "__main__":
    main()
