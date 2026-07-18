from html import escape
from typing import Any

def format_hotels(hotels):
    lines = ["Hotels:"]
    for hotel in hotels:
        result_id = hotel.get("_id", "Unknown ID")
        name = hotel.get("name") or "Unknown Hotel"
        city = hotel.get("city") or hotel.get("location", {}).get("city", "")
        price_per_night = hotel.get("pricePerNight") or "Price not available"
        currency = hotel.get("currency", "")
        lines.append(
            f"{result_id}: {name} in {city} - "
            f"{currency} {price_per_night} per night"
        )
    return "\n".join(lines)

def format_flights(flights):
    lines = ["Flights:"]
    for flight in flights:
        result_id = flight.get("_id", "Unknown ID")
        airline = flight.get("airline", "Unknown Airline")
        flight_number = flight.get("flightNumber", "Unknown Flight Number")
        origin = flight.get("origin", {}).get("airport", "Unknown Origin")
        destination = flight.get("destination", {}).get("airport", "Unknown Destination")
        flight_date = flight.get("flightDate", "Unknown Date")
        departure_time = flight.get("departureTime", "Unknown Departure Time")
        arrival_time = flight.get("arrivalTime", "Unknown Arrival Time")
        price = flight.get("price", "Unknown Price")
        currency = flight.get("currency", "Unknown Currency")
        available_seats = flight.get("availableSeats", "Unknown Available Seats")
        lines.append(
            f"{result_id}: {airline} {flight_number} from {origin} to {destination} "
            f"on {flight_date} {departure_time} - {arrival_time} "
            f"- {currency} {price} - {available_seats} seats"
        )
    return "\n".join(lines)

def format_chat_response(data: dict[str, Any]) -> str:
    chat_text = str(
        data.get("response", "No response returned.")
    )

    parts = [chat_text]

    flights = data.get("flights") or []
    hotels = data.get("hotels") or []

    if flights:
        parts.append(format_flights(flights))

    if hotels:
        parts.append(format_hotels(hotels))

    return "\n\n".join(parts)

def render_progress(events, done=False, error=False):
    if not events:
        return """
        <div class="progress-panel">
            <div class="progress-title">Agent progress</div>
            <div class="progress-empty">No active request.</div>
        </div>
        """

    rows = []

    for index, event in enumerate(events):
        is_last = index == len(events) - 1
        stage = escape(event.get("stage", "working"))
        message = escape(event.get("message", "Working..."))

        if error and is_last:
            icon = '<div class="progress-error">!</div>'
        elif done or not is_last:
            icon = '<div class="progress-check">&#10003;</div>'
        else:
            icon = '<div class="progress-spinner"></div>'

        rows.append(
            f"""
            <div class="progress-step">
                {icon}
                <div>
                    <div class="progress-stage">{stage}</div>
                    <div class="progress-message">{message}</div>
                </div>
            </div>
            """
        )

    return f"""
    <div class="progress-panel">
        <div class="progress-title">Agent progress</div>
        {''.join(rows)}
    </div>
    """

def render_results_panel(results_state):
    hotels = results_state.get("hotels", [])
    flights = results_state.get("flights", [])
    expanded = results_state.get("expanded", False)

    if not hotels and not flights:
        return """
        <div class="progress-panel">
            <div class="progress-title">Travel results</div>
            <div class="progress-empty">No hotel or flight results yet.</div>
        </div>
        """

    if hotels:
        items = hotels if expanded else hotels[:5]
        rows = []

        for hotel in items:
            name = escape(str(hotel.get("name", "Unknown hotel")))
            city = escape(str(hotel.get("city", "Unknown city")))
            price = escape(str(hotel.get("pricePerNight", "N/A")))
            currency = escape(str(hotel.get("currency", "USD")))
            rooms = escape(str(hotel.get("availableRooms", "N/A")))
            stars = escape(str(hotel.get("starRating", "N/A")))

            rows.append(
                f"""
                <div class="result-item">
                    <div class="result-name">{name}</div>
                    <div class="result-meta">{city} | {stars} stars | {currency} {price}/night | {rooms} rooms</div>
                </div>
                """
            )

        count_text = f"Showing {len(items)} of {len(hotels)} hotels"

    else:
        items = flights if expanded else flights[:5]
        rows = []

        for flight in items:
            airline = escape(str(flight.get("airline", "Unknown airline")))
            number = escape(str(flight.get("flightNumber", "N/A")))
            origin = flight.get("origin", {})
            destination = flight.get("destination", {})
            origin_code = escape(str(origin.get("airport", "N/A")))
            destination_code = escape(str(destination.get("airport", "N/A")))
            date = escape(str(flight.get("flightDate", "Unknown date")))
            price = escape(str(flight.get("price", "N/A")))
            currency = escape(str(flight.get("currency", "USD")))

            rows.append(
                f"""
                <div class="result-item">
                    <div class="result-name">{airline} {number}</div>
                    <div class="result-meta">{origin_code} to {destination_code} | {date} | {currency} {price}</div>
                </div>
                """
            )

        count_text = f"Showing {len(items)} of {len(flights)} flights"

    return f"""
    <div class="progress-panel">
        <div class="progress-title">Travel results</div>
        <div class="progress-empty">{count_text}</div>
        {''.join(rows)}
    </div>
    """

def toggle_results(results_state):
    if results_state is None:
        results_state = {"hotels": [], "flights": [], "expanded": False}

    results_state = {
        **results_state,
        "expanded": not results_state.get("expanded", False),
    }

    return render_results_panel(results_state), results_state
