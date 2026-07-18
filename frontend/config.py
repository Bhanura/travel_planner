import os

from dotenv import load_dotenv


load_dotenv()

INTERNAL_PORT = os.environ.get("PORT", "8000")
DEFAULT_API_URL = f"http://127.0.0.1:{INTERNAL_PORT}"

API_BASE_URL = os.environ.get(
    "TRAVEL_PLANNER_API_URL",
    DEFAULT_API_URL,
).rstrip("/")

CHAT_URL = f"{API_BASE_URL}/chat"
STREAM_URL = f"{API_BASE_URL}/chat/stream"