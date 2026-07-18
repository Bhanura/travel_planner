import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from mcp_servers.provider_utils import get_json, post_json, extract_list

load_dotenv()

FLIGHT_API_BASE = os.getenv("FLIGHT_PROVIDER_BASE_URL", "").strip()

if not FLIGHT_API_BASE:
    raise RuntimeError(
        "FLIGHT_PROVIDER_BASE_URL is required but was not configured."
    )

FLIGHT_API_BASE = FLIGHT_API_BASE.rstrip("/")

mcp = FastMCP("tripweaver-flight-server")

@mcp.tool()
def book_flight(
    flight_id: str,
    passenger_name: str,
    passenger_email: str,
) -> dict:
    """
    Book a flight.

    Args:
        flight_id: Flight ID returned by list_flights or search_flights.
        passenger_name: Full name of the passenger.
        passenger_email: Passenger email address.
    """
    payload = {
        "flightId": flight_id,
        "passengerName": passenger_name,
        "passengerEmail": passenger_email,
    }

    data = post_json(f"{FLIGHT_API_BASE}/book", payload=payload)

    return data if isinstance(data, dict) else {"status": "unknown", "raw": data}

@mcp.tool()
def list_flights() -> list[dict]:
    """
    Get a list of all available flights.
    Use this when the user asks to show/list all flights.
    """
    data = get_json(FLIGHT_API_BASE)

    return extract_list(data, "flights")


@mcp.tool()
def search_flights(
    origin: str,
    destination: str,
    date: Optional[str] = None,
) -> list[dict]:
    """
    Search for flights by origin, destination, and optional departure date.

    Args:
        origin: Flight origin airport code. Example: BKK, CMB, SIN.
        destination: Flight destination airport code. Example: BKK, CMB, SIN.
        date: Optional departure date in YYYY-MM-DD format.
    """
    if origin and len(origin) == 3 and origin.isalpha():
        normalized_origin = origin.upper()
    else:
        normalized_origin = origin
    
    if destination and len(destination) == 3 and destination.isalpha():
        normalized_destination = destination.upper()
    else:
        normalized_destination = destination
    
    params = {
        "origin": normalized_origin,
        "destination": normalized_destination,
    }

    if date:
        params["date"] = date

    data = get_json(f"{FLIGHT_API_BASE}/search", params=params)

    return extract_list(data, "flights")

if __name__ == "__main__":
    mcp.run()