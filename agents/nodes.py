from typing import Optional, Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .tools import get_hotels, search_hotel, book_hotel, get_flights, search_flights, book_flight
from .llm import llm
from .prompts import get_system_prompt_for_unknown_node, get_system_prompt_with_history
from .entity import GraphState

class TravelExtraction(BaseModel):
    intent: Literal["hotel", "flight", "unknown"] = Field(
        default="unknown",
        description="Main user intent: hotel, flight, or unknown."
    )

    sub_action: Literal["search", "list_all","book", "general"] = Field(
        default="general",
        description="Action type: search, list_all, book or general."
    )

    city: Optional[str] = Field(
        default=None,
        description="Hotel city name. Example: Mumbai, Colombo, Bangkok."
    )

    check_in: Optional[str] = Field(
        default=None,
        description="Hotel check-in date in YYYY-MM-DD format. Null if not provided."
    )

    check_out: Optional[str] = Field(
        default=None,
        description="Hotel check-out date in YYYY-MM-DD format. Null if not provided."
    )

    origin: Optional[str] = Field(
        default=None,
        description="Flight origin city or airport code. Example: BOM, CMB, Mumbai."
    )

    destination: Optional[str] = Field(
        default=None,
        description="Flight destination city or airport code. Example: DEL, BKK, Delhi."
    )

    flight_date: Optional[str] = Field(
        default=None,
        description="Flight date in YYYY-MM-DD format. Null if not provided."
    )

    hotel_id: Optional[str] = Field(
        default=None,
        description="ID of the hotel to book. Null if not provided."
    )

    guest_name: Optional[str] = Field(
        default=None,
        description="Guest full name for hotel booking. Null if not provided."
    )

    guest_email: Optional[str] = Field(
        default=None,
        description="Guest email for hotel booking. Null if not provided."
    )

    room_type: Optional[str] = Field(
        default=None,
        description="Hotel room type such as single, double, or suite. Null if not provided."
    )

    flight_id: Optional[str] = Field(
        default=None,
        description="ID of the flight to book. Null if not provided."
    )

    passenger_name: Optional[str] = Field(
        default=None,
        description="Passenger full name for flight booking. Null if not provided."
    )

    passenger_email: Optional[str] = Field(
        default=None,
        description="Passenger email for flight booking. Null if not provided."
    )

travel_extractor = llm.with_structured_output(TravelExtraction)

FIELD_LABELS = {
    "hotel_id": "hotel ID",
    "guest_name": "guest name",
    "guest_email": "guest email",
    "room_type": "room type",
    "check_in": "check-in date",
    "check_out": "check-out date",
    "flight_id": "flight ID",
    "passenger_name": "passenger name",
    "passenger_email": "passenger email",
    "origin": "departure city or airport",
    "destination": "destination city or airport",
    "city": "city",
}

CITY_TO_AIRPORT = {
    "bangkok": "BKK",
    "mumbai": "BOM",
    "guangzhou": "CAN",
    "cebu": "CEB",
    "jakarta": "CGK",
    "delhi": "DEL",
    "bali": "DPS",
    "hanoi": "HAN",
    "phuket": "HKT",
    "seoul": "ICN",
    "osaka": "KIX",
    "kuala lumpur": "KUL",
    "manila": "MNL",
    "tokyo": "NRT",
    "beijing": "PEK",
    "penang": "PEN",
    "busan": "PUS",
    "shanghai": "PVG",
    "ho chi minh city": "SGN",
    "singapore": "SIN",
}

def _normalize_airport(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    cleaned = value.strip()

    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned.upper()

    return CITY_TO_AIRPORT.get(cleaned.lower(), cleaned)

def _normalize_selection_text(value: Optional[str]) -> str:
    if not value:
        return ""

    return " ".join(value.lower().replace('"', "").replace("'", "").split())

def _resolve_hotel_selection(candidate: Optional[str], hotels: list[dict]) -> Optional[dict]:
    if not candidate or not hotels:
        return None

    candidate_text = _normalize_selection_text(candidate)

    for hotel in hotels:
        hotel_id = _normalize_selection_text(hotel.get("_id"))
        hotel_name = _normalize_selection_text(hotel.get("name"))

        if candidate_text == hotel_id or candidate_text == hotel_name:
            return hotel

    for hotel in hotels:
        hotel_name = _normalize_selection_text(hotel.get("name"))

        if candidate_text in hotel_name or hotel_name in candidate_text:
            return hotel

    return None

def _hotel_summary(hotel: dict) -> str:
    name = hotel.get("name", "selected hotel")
    city = hotel.get("city", "unknown city")
    price = hotel.get("pricePerNight", hotel.get("price", "N/A"))
    currency = hotel.get("currency", "USD")

    return f"{name} in {city} for {currency} {price}/night"

def _hotel_confirmation_message(hotel: dict, details: dict) -> str:
    return (
        "Please confirm this hotel booking: "
        f"{_hotel_summary(hotel)} from {details['check_in_date']} "
        f"to {details['check_out_date']} for {details['guest_name']} "
        f"({details['guest_email']}), room type: {details['room_type']}. "
        "Reply yes to confirm, or tell me what to change."
    )

def _hotel_booking_success_message(result: dict, hotel: Optional[dict]) -> str:
    booking = result.get("booking", {}) if isinstance(result, dict) else {}

    booking_reference = booking.get("bookingReference") or booking.get("bookingId")
    status = booking.get("status", "confirmed")
    total_price = booking.get("totalPrice")

    if hotel:
        hotel_text = _hotel_summary(hotel)
    else:
        hotel_text = "your selected hotel"

    parts = [f"Hotel booking {status} for {hotel_text}."]

    if booking_reference:
        parts.append(f"Booking reference: {booking_reference}.")

    if total_price is not None:
        currency = hotel.get("currency", "USD") if hotel else "USD"
        parts.append(f"Total price: {currency} {total_price}.")

    return " ".join(parts)

AFFIRMATIVE_WORDS = {
    "yes",
    "yeah",
    "yep",
    "sure",
    "confirm",
    "confirmed",
    "ok",
    "okay",
    "book it",
    "go ahead",
}

def _is_affirmative(message: str) -> bool:
    cleaned = _normalize_selection_text(message)
    words = set(cleaned.replace(",", " ").replace(".", " ").split())

    return (
        cleaned in AFFIRMATIVE_WORDS
        or bool(words & AFFIRMATIVE_WORDS)
        or "go ahead" in cleaned
        or "book it" in cleaned
        or "do it" in cleaned
    )

def _format_missing_fields(missing: list[str]) -> str:
    labels = [FIELD_LABELS.get(field, field) for field in missing]

    if len(labels) == 1:
        return labels[0]

    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"

    return f"{', '.join(labels[:-1])}, and {labels[-1]}"

def _missing_details_message(action: str, missing: list[str]) -> str:
    return (
        f"I can help with that {action}. "
        f"I still need your {_format_missing_fields(missing)}."
    )

def _service_error_response(service: str) -> dict:
    return {
        "hotel_results": [],
        "flight_results": [],
        "response_text": (
            f"I'm having trouble reaching the {service} service right now. "
            "Please try again in a moment, or continue with another travel request."
        ),
    }

def router(state: GraphState) -> dict:
    user_message = state["messages"][-1]
    history_messages = state["messages"][:-1]

    pending_hotel_booking = state.get("pending_hotel_booking")

    if (
        pending_hotel_booking
        and pending_hotel_booking.get("awaiting_confirmation")
        and _is_affirmative(user_message)
    ):
        details = pending_hotel_booking.get("details", {})
        hotel = pending_hotel_booking.get("hotel", {})

        return {
            "intent": "hotel",
            "sub_action": "book",
            "city": None,
            "check_in": details.get("check_in_date"),
            "check_out": details.get("check_out_date"),
            "origin": None,
            "destination": None,
            "flight_date": None,
            "hotel_id": hotel.get("_id"),
            "guest_name": details.get("guest_name"),
            "guest_email": details.get("guest_email"),
            "room_type": details.get("room_type"),
            "flight_id": None,
            "passenger_name": None,
            "passenger_email": None,
            "hotel_results": [],
            "flight_results": [],
            "last_hotel_results": state.get("last_hotel_results", []),
            "last_flight_results": state.get("last_flight_results", []),
            "pending_hotel_booking": pending_hotel_booking,
            "pending_flight_booking": state.get("pending_flight_booking"),
            "booking_confirmed": True,
            "response_text": "",
        }

    origin = None
    destination = None
    
    system_prompt = get_system_prompt_with_history("\n".join(history_messages))

    invocation_messages = [SystemMessage(content=system_prompt)]
    for i in range(0, len(history_messages), 2):
        invocation_messages.append(HumanMessage(content=history_messages[i]))
        if i + 1 < len(history_messages):
            invocation_messages.append(AIMessage(content=history_messages[i + 1]))
    invocation_messages.append(HumanMessage(content=user_message))

    try:
        extracted = travel_extractor.invoke(invocation_messages)

        data = extracted.dict()
        origin = _normalize_airport(data.get("origin"))
        destination = _normalize_airport(data.get("destination"))
        print("Router extraction debug:", data)
        print("Router normalized route debug:", {"origin": origin, "destination": destination})

    except Exception:
        data = {
            "intent": "unknown",
            "sub_action": "general",
            "city": None,
            "check_in": None,
            "check_out": None,
            "origin": None,
            "destination": None,
            "flight_date": None,
            "hotel_id": None,
            "guest_name": None,
            "guest_email": None,
            "room_type": None,
            "flight_id": None,
            "passenger_name": None,
            "passenger_email": None,
        }

    return {
        "intent": data.get("intent", "unknown"),
        "sub_action": data.get("sub_action", "general"),

        "city": data.get("city"),
        "check_in": data.get("check_in"),
        "check_out": data.get("check_out"),

        "origin": origin,
        "destination": destination,
        "flight_date": data.get("flight_date"),

        "hotel_id": data.get("hotel_id"),
        "guest_name": data.get("guest_name"),
        "guest_email": data.get("guest_email"),
        "room_type": data.get("room_type"),

        "flight_id": data.get("flight_id"),
        "passenger_name": data.get("passenger_name"),
        "passenger_email": data.get("passenger_email"),

        "hotel_results": [],
        "flight_results": [],
        "response_text": "",
    }

def _format_hotel(hotel: dict) -> str:
    name = hotel.get("name", "Unknown hotel")

    city_data = hotel.get("city", "unknown city")
    if isinstance(city_data, dict):
        city = city_data.get("name", "unknown city")
    else:
        city = city_data

    stars = hotel.get("rating", hotel.get("starRating", "N/A"))
    price = hotel.get("price", hotel.get("pricePerNight", "N/A"))
    currency = hotel.get("currency", "USD")

    available = hotel.get(
        "available_rooms",
        hotel.get("availableRooms", hotel.get("available", "N/A"))
    )

    return (
        f"{name} in {city}, "
        f"{stars} stars - {currency} {price}/night - "
        f"{available} rooms"
    )

def _format_flight(flight: dict) -> str:
    airline = flight.get("airline", "Unknown airline")

    number = flight.get(
        "flightNumber",
        flight.get("flight_number", flight.get("flightNo", "N/A"))
    )

    origin_data = flight.get("origin", "unknown")
    destination_data = flight.get("destination", "unknown")

    if isinstance(origin_data, dict):
        origin = origin_data.get("airport", origin_data.get("city", "unknown"))
    else:
        origin = origin_data

    if isinstance(destination_data, dict):
        destination = destination_data.get("airport", destination_data.get("city", "unknown"))
    else:
        destination = destination_data

    flight_date = flight.get(
        "flightDate",
        flight.get("date", flight.get("departure_date", "unknown"))
    )

    departure_time = flight.get(
        "departureTime",
        flight.get("departure_time", "N/A")
    )

    arrival_time = flight.get(
        "arrivalTime",
        flight.get("arrival_time", "N/A")
    )

    price = flight.get("price", "N/A")
    currency = flight.get("currency", "USD")

    seats = flight.get(
        "availableSeats",
        flight.get("available_seats", flight.get("seats", "N/A"))
    )

    return (
        f"{airline} {number} from {origin} to {destination} "
        f"on {flight_date}, {departure_time} - {arrival_time} "
        f"- {currency} {price} - {seats} seats"
    )

def hotel_node(state: GraphState) -> dict:
    city = state.get("city")
    check_in = state.get("check_in")
    check_out = state.get("check_out")
    print("Hotel node last hotels:", len(state.get("last_hotel_results", [])))

    if state.get("sub_action") == "book":
        hotel_id = state.get("hotel_id")
        pending_booking = state.get("pending_hotel_booking") or {}

        selected_hotel = _resolve_hotel_selection(
            hotel_id,
            state.get("last_hotel_results", []),
        ) or pending_booking.get("hotel")


        if selected_hotel:
            hotel_id = selected_hotel.get("_id")

        print("Resolved selected hotel:", selected_hotel.get("name") if selected_hotel else None)
        guest_name = state.get("guest_name")
        guest_email = state.get("guest_email")
        room_type = state.get("room_type")
        check_in_date = state.get("check_in")
        check_out_date = state.get("check_out")

        pending_details = pending_booking.get("details", {})

        guest_name = guest_name or pending_details.get("guest_name")
        guest_email = guest_email or pending_details.get("guest_email")
        room_type = room_type or pending_details.get("room_type")
        check_in_date = check_in_date or pending_details.get("check_in_date")
        check_out_date = check_out_date or pending_details.get("check_out_date")

        print("Booking details after pending merge:", {
            "hotel_id": hotel_id,
            "guest_name": guest_name,
            "guest_email": guest_email,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "room_type": room_type,
        })

        missing = [
            field
            for field, value in [
                ("hotel_id", hotel_id),
                ("guest_name", guest_name),
                ("guest_email", guest_email),
                ("check_in", check_in_date),
                ("check_out", check_out_date),
                ("room_type", room_type),
            ]
            if not value
        ]

        if missing:
            pending_hotel_booking = None

            if selected_hotel and not state.get("booking_confirmed"):
                pending_hotel_booking = {
                    "hotel": selected_hotel,
                    "details": {
                        "hotel_id": hotel_id,
                        "guest_name": guest_name,
                        "guest_email": guest_email,
                        "check_in_date": check_in_date,
                        "check_out_date": check_out_date,
                        "room_type": room_type,
                    },
                    "awaiting_confirmation": False,
                }

            return {
                "hotel_results": [],
                "flight_results": [],
                "pending_hotel_booking": pending_hotel_booking,
                "response_text": _missing_details_message("hotel booking", missing),
            }
        
        details = {
            "hotel_id": hotel_id,
            "guest_name": guest_name,
            "guest_email": guest_email,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "room_type": room_type,
        }

        if selected_hotel and not state.get("booking_confirmed"):
            pending_hotel_booking = {
                "hotel": selected_hotel,
                "details": details,
                "awaiting_confirmation": True,
            }

            return {
                "hotel_results": [],
                "flight_results": [],
                "pending_hotel_booking": pending_hotel_booking,
                "response_text": _hotel_confirmation_message(selected_hotel, details),
            }

        print("Hotel booking debug:", {
            "hotel_id": hotel_id,
            "guest_email": guest_email,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "room_type": room_type,
        })

        try:
            result = book_hotel.invoke(
                {
                    "hotel_id": hotel_id,
                    "guest_name": guest_name,
                    "guest_email": guest_email,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "room_type": room_type,
                }
            )
        except Exception as exc:
            print(f"Hotel booking failed: {type(exc).__name__}: {exc}")
            return _service_error_response("hotel")

    elif state.get("sub_action") == "list_all":
        try:
            result = get_hotels.invoke({})
        except Exception as exc:
            print(f"Failed to list hotels: {type(exc).__name__}: {exc}")
            return _service_error_response("hotel")

    elif city:
        params = {
            "city": city,
        }

        if check_in:
            params["checkIn"] = check_in

        if check_out:
            params["checkOut"] = check_out

        try:
            result = search_hotel.invoke(params)
            print("Hotel search debug:", params)
        except Exception as exc:
            print(f"Failed to search hotels: {type(exc).__name__}: {exc}")
            return _service_error_response("hotel")

    else:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": _missing_details_message("hotel search", ["city"]),
        }

    if state.get("sub_action") == "book":
        if isinstance(result, dict):
            confirmation = _hotel_booking_success_message(result, selected_hotel)
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": confirmation,
            }

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": "Hotel booking completed.",
        }

    if isinstance(result, dict):
        hotel_results = result.get("hotels", [])
    elif isinstance(result, list):
        hotel_results = result
    else:
        hotel_results = []

    if not hotel_results:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": (
                "I couldn't find any hotels. "
                "Try searching by city, for example: 'available hotels in Mumbai'."
            ),
        }

    return {
        "hotel_results": hotel_results,
        "flight_results": [],
        "response_text": "",
    }

def flight_node(state: GraphState) -> dict:
    origin = state.get("origin")
    destination = state.get("destination")
    flight_date = state.get("flight_date")

    if state.get("sub_action") == "book":
        flight_id = state.get("flight_id")
        passenger_name = state.get("passenger_name")
        passenger_email = state.get("passenger_email")

        missing = [
            field
            for field, value in [
                ("flight_id", flight_id),
                ("passenger_name", passenger_name),
                ("passenger_email", passenger_email),
            ]
            if not value
        ]

        if missing:
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": _missing_details_message("flight booking", missing),
            }

        print("Flight booking debug:", {
            "flight_id": flight_id,
            "passenger_name": passenger_name,
            "passenger_email": passenger_email,
        })

        try:
            result = book_flight.invoke(
                {
                    "flight_id": flight_id,
                    "passenger_name": passenger_name,
                    "passenger_email": passenger_email,
                }
            )
        except Exception as exc:
            print(f"Failed to book flight: {type(exc).__name__}: {exc}")
            return _service_error_response("flight")

    elif state.get("sub_action") == "list_all":
        try:
            result = get_flights.invoke({})
        except Exception as exc:
            print(f"Failed to list flights: {type(exc).__name__}: {exc}")
            return _service_error_response("flight")

    elif origin and destination:
        params = {
            "origin": origin,
            "destination": destination,
        }

        if flight_date:
            params["date"] = flight_date

        try:
            result = search_flights.invoke(params)
            print("Flight search debug:", params)
        except Exception as exc:
            print(f"Failed to search flights: {type(exc).__name__}: {exc}")
            return _service_error_response("flight")

    elif origin or destination:
        missing = []
        
        if not origin:
            missing.append("origin")
        
        if not destination:
            missing.append("destination")

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": _missing_details_message("flight search", missing),
        }

    else:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": _missing_details_message("flight search", ["origin", "destination"]),
        }

    if state.get("sub_action") == "book":
        if isinstance(result, dict):
            confirmation = result.get("message") or result.get("status") or "Flight booking completed."
            return {
                "hotel_results": [],
                "flight_results": [],
                "response_text": confirmation,
            }

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": "Flight booking completed.",
        }

    if isinstance(result, dict):
        flight_results = result.get("flights", [])
    elif isinstance(result, list):
        flight_results = result
    else:
        flight_results = []

    if not flight_results:
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": (
                "I couldn't find flights matching your request. "
                "Try another route or ask for all flights."
            ),
        }

    return {
        "hotel_results": [],
        "flight_results": flight_results,
        "response_text": "",
    }

def unknown_node(state: GraphState) -> dict:
    user_message = state["messages"][-1]
    history_messages = state["messages"][:-1]

    system_prompt = get_system_prompt_for_unknown_node("\n".join(history_messages))

    invocation_messages = [SystemMessage(content=system_prompt)]
    for i in range(0, len(history_messages), 2):
        invocation_messages.append(HumanMessage(content=history_messages[i]))
        if i + 1 < len(history_messages):
            invocation_messages.append(AIMessage(content=history_messages[i + 1]))
    invocation_messages.append(HumanMessage(content=user_message))

    try:
        response = llm.invoke(invocation_messages)

        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": response.content,
        }

    except Exception as e:
        print(f"Failed to generate response: {type(e).__name__}: {e}")
        return {
            "hotel_results": [],
            "flight_results": [],
            "response_text": f"I couldn't understand your request clearly. Error: {str(e)}",
        }

def generate_response(state: GraphState) -> dict:
    if state.get("response_text"):
        return {
            "response_text": state["response_text"]
        }

    hotel_results = state.get("hotel_results", [])
    flight_results = state.get("flight_results", [])

    if hotel_results:
        count = len(hotel_results)
        lines = [_format_hotel(hotel) for hotel in hotel_results[:5]]

        return {
            "response_text": (
                f"I found {count} hotel option{'s' if count != 1 else ''}:\n"
                + "\n".join(lines)
            )
        }

    if flight_results:
        count = len(flight_results)
        lines = [_format_flight(flight) for flight in flight_results[:5]]

        return {
            "response_text": (
                f"I found {count} flight option{'s' if count != 1 else ''}:\n"
                + "\n".join(lines)
            )
        }

    return {
        "response_text": "I couldn't find matching travel options."
    }

def route_after_extraction(state: GraphState) -> str:
    intent = state.get("intent", "unknown")

    if intent == "hotel":
        return "hotel"

    if intent == "flight":
        return "flight"

    return "unknown"