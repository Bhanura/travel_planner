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

def _post_json(url: str, data: Optional[dict] = None) -> Any:
    with httpx.Client(timeout=15) as client:
        response = client.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
@mcp.tool()
def book_hotel(
    hotel_id: str,
    guest_name: str,
    guest_email: str,
    check_in_date: str,
    check_out_date: str,
    room_type: str,
) -> dict:
    """
    Book a hotel room.

    Args:
        hotel_id: Hotel ID returned by list_hotels or search_hotels.
        guest_name: Full name of the guest.
        guest_email: Guest email address.
        check_in_date: Check-in date in YYYY-MM-DD format.
        check_out_date: Check-out date in YYYY-MM-DD format.
        room_type: Room type such as single, double, or suite.
    """
    payload = {
        "hotelId": hotel_id,
        "guestName": guest_name,
        "guestEmail": guest_email,
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
        "roomType": room_type,
    }

    data = _post_json(f"{HOTEL_API_BASE}/book", data=payload)

    return data if isinstance(data, dict) else {"status": "unknown", "raw": data}

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

@mcp.tool()
def search_hotels(
    city: str,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
) -> list[dict]:
    """
    Search hotels by city with optional check-in and check-out dates.

    Args:
        city: City name to search hotels in, such as Bangkok or Colombo.
        check_in: Optional check-in date in YYYY-MM-DD format.
        check_out: Optional check-out date in YYYY-MM-DD format.
    """
    params = {"city": city}

    if check_in:
        params["checkIn"] = check_in
    
    if check_out:
        params["checkOut"] = check_out

    data = _get_json(f"{HOTEL_API_BASE}/search", params=params)

    if isinstance(data, dict):
        hotels = data.get("hotels", [])
        return hotels if isinstance(hotels, list) else []
    
    if isinstance(data, list):
        return data
    
    return []


if __name__ == "__main__":
    mcp.run()