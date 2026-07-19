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

def _transcript_content_text(content) -> str:
    """
    Extract visible text from Gradio chat content.

    Unknown content shapes are ignored instead of exposing
    their Python representation in the transcript.
    """
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return ""

    text_parts = []

    for block in content:
        if isinstance(block, str):
            text_parts.append(block)
            continue

        if not isinstance(block, dict):
            continue

        block_text = block.get("text")

        if isinstance(block_text, str):
            text_parts.append(block_text)

    return "".join(text_parts)


def format_test_transcript(history) -> str:
    """
    Build a temporary plain-text transcript for
    flight-booking UI tests.

    This must contain only visible user and assistant
    messages, never internal graph state or prompts.
    """
    if not history:
        return "No conversation has been recorded yet."

    transcript_parts = [
        "TRIPWEAVER BOOKING TEST TRANSCRIPT",
        "Use test passenger details only.",
    ]

    for message in history:
        if not isinstance(message, dict):
            continue

        role = str(message.get("role", "")).lower()

        if role not in {"user", "assistant"}:
            continue

        content = _transcript_content_text(
            message.get("content", "")
        ).strip()

        if not content:
            continue

        transcript_parts.append(
            f"{role.upper()}:\n{content}"
        )

    return "\n\n".join(transcript_parts)

def render_progress(events, done=False, error=False):
    if not events:
        return """
        <section
            class="tw-panel tw-progress-panel"
            aria-label="Agent progress"
            aria-live="polite"
        >
            <div class="tw-panel-header">
                <div class="tw-panel-heading">
                    <span class="tw-panel-icon">✦</span>
                    <div>
                        <div class="tw-panel-kicker">LIVE WORKFLOW</div>
                        <div class="tw-panel-title">Agent journey</div>
                    </div>
                </div>
                <span class="tw-status-pill is-idle">Ready</span>
            </div>

            <div class="tw-empty-state">
                <div class="tw-empty-icon">🧭</div>
                <div class="tw-empty-title">Ready to explore</div>
                <div class="tw-empty-copy">
                    Your agent activity will appear here
                    after you send a travel request.
                </div>
            </div>
        </section>
        """

    rows = []

    for index, event in enumerate(events):
        is_last = index == len(events) - 1
        stage_value = str(event.get("stage", "working"))
        stage = escape(
            stage_value.replace("_", " ").title()
        )
        message = escape(
            str(event.get("message", "Working..."))
        )

        if error and is_last:
            status_class = "is-error"
            status_content = "!"
        elif done or not is_last:
            status_class = "is-complete"
            status_content = "✓"
        else:
            status_class = "is-active"
            status_content = ""

        rows.append(
            f"""
            <div class="tw-progress-step">
                <div class="tw-progress-track">
                    <div class="tw-step-icon {status_class}">
                        {status_content}
                    </div>
                </div>

                <div class="tw-step-copy">
                    <div class="tw-step-stage">{stage}</div>
                    <div class="tw-step-message">{message}</div>
                </div>
            </div>
            """
        )

    pill_class = "is-error" if error else (
        "is-complete" if done else "is-active"
    )
    pill_text = "Needs attention" if error else (
        "Complete" if done else "Working"
    )

    return f"""
    <section
        class="tw-panel tw-progress-panel"
        aria-label="Agent progress"
        aria-live="polite"
    >
        <div class="tw-panel-header">
            <div class="tw-panel-heading">
                <span class="tw-panel-icon">✦</span>
                <div>
                    <div class="tw-panel-kicker">LIVE WORKFLOW</div>
                    <div class="tw-panel-title">Agent journey</div>
                </div>
            </div>

            <span class="tw-status-pill {pill_class}">
                {pill_text}
            </span>
        </div>

        <div class="tw-progress-list">
            {''.join(rows)}
        </div>
    </section>
    """

def render_results_panel(results_state):
    results_state = results_state or {
        "hotels": [],
        "flights": [],
        "expanded": False,
    }

    hotels = results_state.get("hotels", [])
    flights = results_state.get("flights", [])
    expanded = results_state.get("expanded", False)

    if not hotels and not flights:
        return """
        <section
            class="tw-panel tw-results-panel"
            aria-label="Travel results"
        >
            <div class="tw-panel-header">
                <div class="tw-panel-heading">
                    <span class="tw-panel-icon is-sunset">⌖</span>
                    <div>
                        <div class="tw-panel-kicker">YOUR MATCHES</div>
                        <div class="tw-panel-title">Travel results</div>
                    </div>
                </div>
            </div>

            <div class="tw-empty-state">
                <div class="tw-empty-icon">🗺️</div>
                <div class="tw-empty-title">No matches yet</div>
                <div class="tw-empty-copy">
                    Hotel and flight options will appear here
                    after TripWeaver completes a search.
                </div>
            </div>
        </section>
        """

    rows = []

    if hotels:
        items = hotels if expanded else hotels[:5]
        result_kind = "Hotel options"

        for result_number, hotel in enumerate(items, start=1):
            result_id = escape(
                str(hotel.get("_id", "Not available"))
            )
            name = escape(
                str(hotel.get("name", "Unknown hotel"))
            )
            city = escape(
                str(hotel.get("city", "Unknown city"))
            )
            price = escape(
                str(hotel.get("pricePerNight", "N/A"))
            )
            currency = escape(
                str(hotel.get("currency", "USD"))
            )
            rooms = escape(
                str(hotel.get("availableRooms", "N/A"))
            )
            stars = escape(
                str(hotel.get("starRating", "N/A"))
            )

            rows.append(
                f"""
                <article class="tw-result-card">
                    <div class="tw-result-number">
                        {result_number:02d}
                    </div>

                    <div class="tw-result-body">
                        <div class="tw-result-topline">
                            <div class="tw-result-name">{name}</div>
                            <span class="tw-result-price">
                                {currency} {price}
                            </span>
                        </div>

                        <div class="tw-result-location">
                            📍 {city}
                        </div>

                        <div class="tw-result-facts">
                            <span>★ {stars} rating</span>
                            <span>🛏 {rooms} rooms</span>
                            <span>per night</span>
                        </div>

                        <div class="tw-result-id">
                            Selection ID: {result_id}
                        </div>
                    </div>
                </article>
                """
            )

        count_text = (
            f"Showing {len(items)} of {len(hotels)} hotels"
        )

    else:
        items = flights if expanded else flights[:5]
        result_kind = "Flight options"

        for result_number, flight in enumerate(items, start=1):
            result_id = escape(
                str(flight.get("_id", "Not available"))
            )
            airline = escape(
                str(flight.get("airline", "Unknown airline"))
            )
            number = escape(
                str(flight.get("flightNumber", "N/A"))
            )

            origin = flight.get("origin", {}) or {}
            destination = flight.get("destination", {}) or {}

            origin_code = escape(
                str(origin.get("airport", "N/A"))
            )
            destination_code = escape(
                str(destination.get("airport", "N/A"))
            )
            date = escape(
                str(flight.get("flightDate", "Unknown date"))
            )
            departure = escape(
                str(flight.get("departureTime", "N/A"))
            )
            arrival = escape(
                str(flight.get("arrivalTime", "N/A"))
            )
            price = escape(
                str(flight.get("price", "N/A"))
            )
            currency = escape(
                str(flight.get("currency", "USD"))
            )
            seats = escape(
                str(flight.get("availableSeats", "N/A"))
            )

            rows.append(
                f"""
                <article class="tw-result-card">
                    <div class="tw-result-number">
                        {result_number:02d}
                    </div>

                    <div class="tw-result-body">
                        <div class="tw-result-topline">
                            <div class="tw-result-name">
                                {airline} {number}
                            </div>
                            <span class="tw-result-price">
                                {currency} {price}
                            </span>
                        </div>

                        <div class="tw-flight-route">
                            <strong>{origin_code}</strong>
                            <span>→</span>
                            <strong>{destination_code}</strong>
                        </div>

                        <div class="tw-result-facts">
                            <span>📅 {date}</span>
                            <span>🕒 {departure}–{arrival}</span>
                            <span>💺 {seats} seats</span>
                        </div>

                        <div class="tw-result-id">
                            Selection ID: {result_id}
                        </div>
                    </div>
                </article>
                """
            )

        count_text = (
            f"Showing {len(items)} of {len(flights)} flights"
        )

    return f"""
    <section
        class="tw-panel tw-results-panel"
        aria-label="Travel results"
    >
        <div class="tw-panel-header">
            <div class="tw-panel-heading">
                <span class="tw-panel-icon is-sunset">⌖</span>
                <div>
                    <div class="tw-panel-kicker">YOUR MATCHES</div>
                    <div class="tw-panel-title">{result_kind}</div>
                </div>
            </div>
        </div>

        <div class="tw-results-summary">{count_text}</div>

        <div class="tw-results-list">
            {''.join(rows)}
        </div>
    </section>
    """

def toggle_results(results_state):
    if results_state is None:
        results_state = {
            "hotels": [],
            "flights": [],
            "expanded": False,
        }

    results_state = {
        **results_state,
        "expanded": not results_state.get(
            "expanded",
            False,
        ),
    }

    button_label = (
        "Collapse results  ↑"
        if results_state["expanded"]
        else "See all results  ↓"
    )

    return (
        render_results_panel(results_state),
        results_state,
        button_label,
    )
