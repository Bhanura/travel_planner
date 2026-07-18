import json
import os
import uuid
from dotenv import load_dotenv
from urllib.request import Request, urlopen
import gradio as gr
from html import escape

load_dotenv()

internal_port = os.environ.get("PORT", "8000")
default_api_url = f"http://127.0.0.1:{internal_port}"

API_BASE_URL = os.environ.get(
    "TRAVEL_PLANNER_API_URL",
    default_api_url,
).rstrip("/")

CHAT_URL = f"{API_BASE_URL}/chat"
STREAM_URL = f"{API_BASE_URL}/chat/stream"

APP_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.orange,
    neutral_hue=gr.themes.colors.slate,
    radius_size=gr.themes.sizes.radius_lg,
)

APP_CSS = """
:root {
    --tw-ocean-950: #062a46;
    --tw-ocean-900: #073b61;
    --tw-ocean-700: #086b9c;
    --tw-sky-400: #38bdf8;
    --tw-sunset-500: #f97316;
    --tw-sunset-400: #fb923c;
    --tw-sand-50: #fffaf3;
    --tw-white: #ffffff;
}

.tw-hero {
    position: relative;
    min-height: 310px;
    overflow: hidden;
    display: flex;
    align-items: center;
    padding: 48px;
    margin-bottom: 24px;
    border-radius: 24px;
    color: var(--tw-white);
    box-shadow: 0 24px 60px rgba(6, 42, 70, 0.22);
    background-image:
        linear-gradient(
            90deg,
            rgba(6, 42, 70, 0.96) 0%,
            rgba(7, 59, 97, 0.84) 42%,
            rgba(7, 59, 97, 0.30) 72%,
            rgba(249, 115, 22, 0.10) 100%
        ),
        url("/assets/tripweaver-hero.png");
    background-size: cover;
    background-position: center;
}

.tw-hero::after {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    right: -70px;
    bottom: -100px;
    border-radius: 50%;
    background: rgba(251, 146, 60, 0.22);
    filter: blur(12px);
    animation: tw-hero-glow 6s ease-in-out infinite alternate;
}

.tw-hero__content {
    position: relative;
    z-index: 1;
    max-width: 680px;
    animation: tw-hero-enter 700ms ease-out both;
}

.tw-hero__eyebrow {
    display: inline-flex;
    padding: 7px 12px;
    border: 1px solid rgba(255, 255, 255, 0.30);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(8px);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
}

.tw-hero h1 {
    margin: 18px 0 10px;
    color: var(--tw-white);
    font-size: clamp(42px, 7vw, 72px);
    line-height: 0.95;
    letter-spacing: -0.05em;
}

.tw-hero h1 span {
    color: var(--tw-sunset-400);
}

.tw-hero__description {
    max-width: 620px;
    margin: 0;
    color: rgba(255, 255, 255, 0.88);
    font-size: 17px;
    line-height: 1.65;
}

.tw-hero__features {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 22px;
}

.tw-hero__features span {
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(6, 42, 70, 0.60);
    border: 1px solid rgba(255, 255, 255, 0.18);
    font-size: 13px;
}

.tw-hero__signature {
    margin-top: 22px;
    color: rgba(255, 255, 255, 0.72);
    font-size: 13px;
}

.tw-hero__signature strong {
    color: var(--tw-white);
}

@keyframes tw-hero-enter {
    from {
        opacity: 0;
        transform: translateY(16px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes tw-hero-glow {
    from {
        transform: scale(0.90);
        opacity: 0.50;
    }

    to {
        transform: scale(1.08);
        opacity: 0.90;
    }
}

@media (max-width: 768px) {
    .tw-hero {
        min-height: 390px;
        padding: 30px 22px;
        border-radius: 18px;
        background-position: 66% center;
    }

    .tw-hero h1 {
        font-size: 46px;
    }

    .tw-hero__description {
        font-size: 15px;
    }

    .tw-hero__features {
        align-items: flex-start;
        flex-direction: column;
    }
}

@media (prefers-reduced-motion: reduce) {
    .tw-hero__content,
    .tw-hero::after {
        animation: none;
    }

    .tw-quick-action button,
    #tw-send button {
        transition: none;
    }
}

.tw-chat-shell {
    padding: 22px;
    border: 1px solid rgba(56, 189, 248, 0.14);
    border-radius: 22px;
    background:
        linear-gradient(
            145deg,
            rgba(7, 59, 97, 0.38),
            rgba(15, 23, 42, 0.72)
        );
    box-shadow: 0 18px 45px rgba(2, 20, 35, 0.18);
}

.tw-section-heading {
    margin-bottom: 14px;
}

.tw-section-kicker {
    color: var(--tw-sunset-400);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.14em;
}

.tw-section-heading h2 {
    margin: 6px 0;
    color: var(--tw-white);
    font-size: 26px;
}

.tw-section-heading p {
    margin: 0;
    color: rgba(255, 255, 255, 0.65);
    font-size: 14px;
}

.tw-quick-actions {
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 14px;
}

.tw-quick-action {
    min-width: 190px;
    flex: 1 1 190px;
}

.tw-quick-action button {
    border: 1px solid rgba(56, 189, 248, 0.24) !important;
    background: rgba(8, 107, 156, 0.18) !important;
    color: rgba(255, 255, 255, 0.90) !important;
    transition:
        transform 180ms ease,
        border-color 180ms ease,
        background 180ms ease;
}

.tw-quick-action button:hover {
    transform: translateY(-2px);
    border-color: var(--tw-sunset-400) !important;
    background: rgba(249, 115, 22, 0.16) !important;
}

#tw-chatbot {
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.14);
    border-radius: 18px;
    background: rgba(2, 20, 35, 0.34);
}

.tw-message-row {
    align-items: stretch;
    gap: 10px;
    margin-top: 12px;
}

#tw-message textarea {
    border-color: rgba(56, 189, 248, 0.20);
    line-height: 1.5;
}

#tw-message textarea:focus {
    border-color: var(--tw-sunset-400);
    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.12);
}

#tw-send button {
    height: 100%;
    min-height: 58px;
    border: none !important;
    color: white !important;
    font-weight: 700;
    background:
        linear-gradient(
            135deg,
            var(--tw-sunset-500),
            var(--tw-sunset-400)
        ) !important;
    box-shadow: 0 12px 25px rgba(249, 115, 22, 0.20);
    transition:
        transform 180ms ease,
        box-shadow 180ms ease;
}

#tw-send button:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 32px rgba(249, 115, 22, 0.30);
}

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
    with gr.Blocks(
        title="TripWeaver | AI Travel Planner",
        fill_width=True,
    ) as demo:
        session_id = gr.State(str(uuid.uuid4()))

        results_state = gr.State({
            "hotels": [],
            "flights": [],
            "expanded": False,
        })

        gr.HTML(
            """
            <section class="tw-hero" role="banner">
                <div class="tw-hero__content">
                    <div class="tw-hero__eyebrow">
                        MCP-POWERED MULTI-AGENT TRAVEL PLANNER
                    </div>

                    <h1>
                        Trip<span>Weaver</span>
                    </h1>

                    <p class="tw-hero__description">
                        Discover hotels, explore flights, and plan your next
                        journey through one intelligent travel conversation.
                    </p>

                    <div class="tw-hero__features">
                        <span>✈ Natural flight search</span>
                        <span>🏨 Curated hotel options</span>
                        <span>✓ Human-confirmed bookings</span>
                    </div>

                    <div class="tw-hero__signature">
                        Designed &amp; built by
                        <strong>Bhanura Waduge</strong>
                    </div>
                </div>
            </section>
            """
        )


        with gr.Row():
            with gr.Column(
                scale=4,
                min_width=320,
                elem_classes=["tw-chat-shell"],
            ):
                gr.HTML(
                    """
                    <div class="tw-section-heading">
                        <div>
                            <span class="tw-section-kicker">YOUR JOURNEY STARTS HERE</span>
                            <h2>Where would you like to go?</h2>
                            <p>
                                Ask naturally—TripWeaver will choose the right
                                travel agent for you.
                            </p>
                        </div>
                    </div>
                    """
                )

                with gr.Row(elem_classes=["tw-quick-actions"]):
                    hotel_example = gr.Button(
                        "🏨 Find hotels in Bangkok",
                        elem_classes=["tw-quick-action"],
                    )
                    flight_example = gr.Button(
                        "✈️ Fly from Bangkok to Mumbai",
                        elem_classes=["tw-quick-action"],
                    )
                    inspiration_example = gr.Button(
                        "🌴 Plan a weekend in Singapore",
                        elem_classes=["tw-quick-action"],
                    )

                chatbot = gr.Chatbot(
                    height=350,
                    show_label=False,
                    layout="bubble",
                    placeholder=(
                        "Start with a destination, hotel request, "
                        "flight route, or general travel question."
                    ),
                    feedback_options=None,
                    buttons=["copy"],
                    elem_id="tw-chatbot",
                )

                with gr.Row(elem_classes=["tw-message-row"]):
                    message = gr.Textbox(
                        show_label=False,
                        placeholder=(
                            "Tell me where you want to go, your dates, "
                            "or what you would like to book..."
                        ),
                        lines=2,
                        max_lines=5,
                        scale=8,
                        elem_id="tw-message",
                    )

                    submit = gr.Button(
                        "Plan my trip  →",
                        variant="primary",
                        scale=2,
                        elem_id="tw-send",
                    )

                hotel_example.click(
                    lambda: "Find hotels in Bangkok",
                    outputs=[message],
                )

                flight_example.click(
                    lambda: "Find flights from Bangkok to Mumbai",
                    outputs=[message],
                )

                inspiration_example.click(
                    lambda: "Help me plan a weekend trip to Singapore",
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
    port = int(os.environ.get("PORT", "7860"))

    demo.launch(
        css=APP_CSS,
        theme=APP_THEME,
        footer_links=[],
        server_name="0.0.0.0",
        server_port=port,
    )
