import json
import os
import uuid
from dotenv import load_dotenv
from urllib.request import Request, urlopen
import gradio as gr
from html import escape

load_dotenv()

API_BASE_URL = os.environ.get("TRAVEL_PLANNER_API_URL", "http://127.0.0.1:8000").rstrip("/")
CHAT_URL = f"{API_BASE_URL}/chat"
STREAM_URL = f"{API_BASE_URL}/chat/stream"

APP_CSS = """
.progress-panel {
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 12px;
    background: #18181b;
    min-height: 160px;
}

.progress-title {
    font-weight: 700;
    margin-bottom: 10px;
}

.progress-step {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    margin: 10px 0;
    font-size: 14px;
}

.progress-stage {
    color: #a1a1aa;
    font-size: 12px;
    text-transform: uppercase;
}

.progress-message {
    color: #f4f4f5;
}

.progress-empty {
    color: #a1a1aa;
    font-size: 14px;
}

.progress-check {
    color: #22c55e;
    font-weight: 700;
    width: 16px;
}

.progress-error {
    color: #ef4444;
    font-weight: 700;
    width: 16px;
}

.progress-spinner {
    width: 12px;
    height: 12px;
    margin-top: 3px;
    border: 2px solid #60a5fa;
    border-top-color: transparent;
    border-radius: 50%;
    animation: progress-spin 0.8s linear infinite;
}

@keyframes progress-spin {
    to {
        transform: rotate(360deg);
    }
}

.result-item {
    border-top: 1px solid #3f3f46;
    padding: 10px 0;
}

.result-name {
    font-weight: 700;
    color: #f4f4f5;
}

.result-meta {
    color: #a1a1aa;
    font-size: 13px;
    margin-top: 4px;
}
"""

def format_flights(flights):
    lines = ["Flights:"]
    for flight in flights:
        id = flight.get("_id", "Unknown ID")
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
            f"{id}: {airline} {flight_number} from {origin} to {destination} "
            f"on {flight_date} {departure_time} - {arrival_time} "
            f"- {currency} {price} - {available_seats} seats"
        )
    return "\n".join(lines)

def format_hotels(hotels):
    lines = ["Hotels:"]
    for hotel in hotels:
        id = hotel.get("_id", "Unknown ID")
        name = hotel.get("name") or "Unknown Hotel"
        city = hotel.get("city") or hotel.get("location", {}).get("city", "")
        price_per_night = hotel.get("pricePerNight") or "Price not available"
        currency = hotel.get("price") or hotel.get("currency", "")
        lines.append(f"{id}: {name} in {city} - {price_per_night}{currency} per night")
    return "\n".join(lines)

def call_chat_api(message, session_id):
    payload = json.dumps(
        {"message": message, "session_id": session_id}
    ).encode("utf-8")
    request = Request(CHAT_URL, data=payload, headers={"Content-Type": "application/json"})

    try:
        response = urlopen(request, timeout=60)
        data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return f"Unexpected error: {exc}"

    chat_text = data.get("response", "No response returned.")
    parts = [chat_text]

    if data.get("flights"):
        parts.append(format_flights(data["flights"]))
    if data.get("hotels"):
        parts.append(format_hotels(data["hotels"]))

    return "\n\n".join(parts)

def stream_chat_api(message, session_id):
    payload = json.dumps(
        {"message": message, "session_id": session_id}
    ).encode("utf-8")
    
    request = Request(
        STREAM_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urlopen(request, timeout=60) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()

            if not line:
                continue

            yield json.loads(line)

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

def respond(message, history, session_id, results_state):
    if history is None:
        history = []

    if not message.strip():
        yield history, "", render_progress([]), render_results_panel(results_state), results_state
        return

    progress_events = [
        {"stage": "starting", "message": "Starting request..."}
    ]

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": "Starting..."},
    ]

    yield history, "", render_progress(progress_events), render_results_panel(results_state), results_state

    try:
        for event in stream_chat_api(message, session_id):
            event_type = event.get("type")

            if event_type == "activity":
                activity = {
                    "stage": event.get("stage", "working"),
                    "message": event.get("message", "Working..."),
                }

                if progress_events[-1] != activity:
                    progress_events.append(activity)

                history[-1]["content"] = activity["message"]
                yield history, "", render_progress(progress_events), render_results_panel(results_state), results_state

            elif event_type == "message":
                final_message = event.get("content", "No response returned.")
                history[-1]["content"] = final_message
                results_state = {
                    "hotels": event.get("hotels") or [],
                    "flights": event.get("flights") or [],
                    "expanded": False,
                }
                yield history, "", render_progress(progress_events, done=True), render_results_panel(results_state), results_state

            elif event_type == "error":
                error_message = event.get(
                    "message",
                    "Something went wrong. Please try again.",
                )
                progress_events.append({
                    "stage": "error",
                    "message": error_message,
                })
                history[-1]["content"] = error_message
                yield history, "", render_progress(progress_events, error=True), render_results_panel(results_state), results_state

            elif event_type == "done":
                break

    except Exception:
        fallback = call_chat_api(message, session_id)
        progress_events.append({
            "stage": "fallback",
            "message": "Streaming failed. Used normal chat response.",
        })
        history[-1]["content"] = fallback
        yield history, "", render_progress(progress_events, done=True), render_results_panel(results_state), results_state

def main():
    with gr.Blocks() as demo:
        session_id = gr.State(str(uuid.uuid4()))

        results_state = gr.State({
            "hotels": [],
            "flights": [],
            "expanded": False,
        })

        gr.Markdown(
            "# Trip Weaver by Bhanura Waduge\n"
            "Hotels, flights, and travel help through MCP-powered agents."
        )


        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(height=420)
                message = gr.Textbox(
                    label="Your message",
                    placeholder="Find me flights from CAN to HAN on 2025-11-15",
                )

                with gr.Row():
                    hotel_example = gr.Button("Hotels in Bangkok")
                    flight_example = gr.Button("Flights BOM to DEL")
                    booking_example = gr.Button("Book a hotel")

                submit = gr.Button("Send")

                hotel_example.click(
                    lambda: "hotels in Bangkok",
                    outputs=[message],
                )

                flight_example.click(
                    lambda: "find flights from BOM to DEL",
                    outputs=[message],
                )

                booking_example.click(
                    lambda: "I need to book a hotel",
                    outputs=[message],
                )

            with gr.Column(scale=1):
                with gr.Accordion("Agent progress", open=True):
                    progress = gr.HTML(render_progress([]))

                with gr.Accordion("Travel results", open=True):
                    results = gr.HTML(render_results_panel({"hotels": [], "flights": [], "expanded": False}))
                    toggle_results_button = gr.Button("See All / Collapse")

        submit.click(
            respond,
            inputs=[message, chatbot, session_id, results_state],
            outputs=[chatbot, message, progress, results, results_state],
        )
        
        message.submit(
            respond,
            inputs=[message, chatbot, session_id, results_state],
            outputs=[chatbot, message, progress, results, results_state],
        )

        toggle_results_button.click(
            toggle_results,
            inputs=[results_state],
            outputs=[results, results_state],
        )

    return demo


demo = main()


if __name__ == "__main__":
    demo.launch(css=APP_CSS)
