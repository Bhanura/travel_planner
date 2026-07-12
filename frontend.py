import json
import os
from dotenv import load_dotenv
from urllib.request import Request, urlopen
import gradio as gr

load_dotenv()

API_BASE_URL = os.environ.get("TRAVEL_PLANNER_API_URL", "http://127.0.0.1:8000").rstrip("/")
CHAT_URL = f"{API_BASE_URL}/chat"
STREAM_URL = f"{API_BASE_URL}/chat/stream"


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


def call_chat_api(message):
    payload = json.dumps({"message": message}).encode("utf-8")
    request = Request(CHAT_URL, data=payload, headers={"Content-Type": "application/json"})

    try:
        response = urlopen(request, timeout=15)
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


def respond(message, history):
    if history is None:
        history = []

    answer = call_chat_api(message)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return history, history


def main():
    with gr.Blocks() as demo:
        gr.Markdown(
            "# Trip Weaver by Bhanura Waduge\nHotels, flights, and travel help through MCP-powered agents."
        )
        chatbot = gr.Chatbot()
        message = gr.Textbox(label="Your message", placeholder="Find me flights from CAN to HAN on 2025-11-15")
        submit = gr.Button("Send")

        submit.click(respond, inputs=[message, chatbot], outputs=[chatbot, chatbot])
        message.submit(respond, inputs=[message, chatbot], outputs=[chatbot, chatbot])

    demo.launch()


if __name__ == "__main__":
    main()
