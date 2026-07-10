from typing import List, Optional
from langchain_core.tools import tool
from .mcp_client import call_mcp_tool


@tool
def get_hotels() -> List[dict]:
    """
    Get a list of all available hotels through the hotel MCP server.
    Use this when the user asks to show/list all hotels.
    """
    data = call_mcp_tool("hotel", "list_hotels", {})
    return data if isinstance(data, list) else []


@tool
def search_hotel(
    city: str,
    checkIn: Optional[str] = None,
    checkOut: Optional[str] = None,
) -> List[dict]:
    """
    Search for hotels by city and optional check-in/check-out dates through MCP.

    Args:
        city: Hotel city name. Example: Bangkok, Colombo, Singapore.
        checkIn: Optional check-in date in YYYY-MM-DD format.
        checkOut: Optional check-out date in YYYY-MM-DD format.
    """
    params = {"city": city}

    if checkIn:
        params["check_in"] = checkIn

    if checkOut:
        params["check_out"] = checkOut

    data = call_mcp_tool("hotel", "search_hotels", params)
    return data if isinstance(data, list) else []


@tool
def book_hotel(
    hotel_id: str,
    guest_name: str,
    guest_email: str,
    check_in_date: str,
    check_out_date: str,
    room_type: str,
) -> dict:
    """Book a hotel room through the hotel MCP server.

    Args:
        hotel_id: ID of the hotel to book
        guest_name: Full name of the guest
        guest_email: Email of the guest
        check_in_date: Check-in date (YYYY-MM-DD)
        check_out_date: Check-out date (YYYY-MM-DD)
        room_type: Type of room (single, double, suite)
    """
    payload = {
        "hotel_id": hotel_id,
        "guest_name": guest_name,
        "guest_email": guest_email,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "room_type": room_type,
    }

    data = call_mcp_tool("hotel", "book_hotel", payload)
    return data if isinstance(data, dict) else {"status": "unknown", "raw": data}


@tool
def get_flights() -> List[dict]:
    """
    Get a list of all available flights through the flight MCP server.
    Use this when the user asks to show/list all flights.
    """
    data = call_mcp_tool("flight", "list_flights", {})
    return data if isinstance(data, list) else []


@tool
def search_flights(
    origin: str,
    destination: str,
    date: Optional[str] = None,
) -> List[dict]:
    """
    Search for flights by origin, destination, and optional travel date through MCP.

    Args:
        origin: Flight origin city or airport code. Example: CMB, Bangkok.
        destination: Flight destination city or airport code. Example: BKK, Singapore.
        date: Optional flight date in YYYY-MM-DD format.
    """
    params = {
        "origin": origin,
        "destination": destination,
    }

    if date:
        params["date"] = date

    data = call_mcp_tool("flight", "search_flights", params)
    return data if isinstance(data, list) else []


@tool
def book_flight(flight_id: str, passenger_name: str, passenger_email: str) -> dict:
    """Book a flight ticket through the flight MCP server.

    Args:
        flight_id: ID of the flight to book
        passenger_name: Full name of the passenger
        passenger_email: Email of the passenger
    """
    payload = {
        "flight_id": flight_id,
        "passenger_name": passenger_name,
        "passenger_email": passenger_email,
    }

    data = call_mcp_tool("flight", "book_flight", payload)
    return data if isinstance(data, dict) else {"status": "unknown", "raw": data}
