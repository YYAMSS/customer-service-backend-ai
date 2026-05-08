"""
PL-002: Test configuration with BASE_URL and auth placeholder for the edu chat backend.
"""
import os

# The education AI chat backend (edu-service-backend)
BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8012")
API_CHAT = f"{BASE_URL}/api/chat"
API_CHAT_HISTORY = f"{BASE_URL}/api/chat/history"

# Auth token placeholder (the current implementation does not require auth headers,
# but this is here per the test plan for future use)
AUTH_TOKEN_PLACEHOLDER = os.environ.get("TEST_AUTH_TOKEN", "")

# Business service backend (for direct data verification)
BUSINESS_BASE_URL = os.environ.get("TEST_BUSINESS_BASE_URL", "http://127.0.0.1:9001")
