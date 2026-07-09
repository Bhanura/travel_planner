import os
from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

HOTEL_API_BASE = os.getenv(
    "HOTEL_PROVIDER_BASE_URL",
    "https://standing-fish-574.convex.site/hotels",
)

mcp = FastMCP("tripweaver-hotel-server")


def _get_json(url: str, params: Optional[dict] = None) -> Any:
    with httpx.Client(timeout=15) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def list_hotels() -> list[dict]:
    """
    List all available hotels from the configured hotel provider.
    """
    data = _get_json(HOTEL_API_BASE)

    if isinstance(data, dict):
        hotels = data.get("hotels", [])
        return hotels if isinstance(hotels, list) else []

    if isinstance(data, list):
        return data

    return []


if __name__ == "__main__":
    mcp.run()