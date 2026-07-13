import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from entity import ChatRequest, ChatResponse
from agents.tools import get_hotels, get_flights
from agents.graph import graph

conversation_history_messages = []

app = FastAPI()

load_dotenv()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _stream_event(event: dict) -> str:
    return json.dumps(event) + "\n"

def _activity_from_result(result: dict) -> dict:
    response_text = result.get("response_text", "")
    sub_action = result.get("sub_action", "")

    if "I still need" in response_text:
        return {
            "stage": "clarifying",
            "message": "Checking what details are missing...",
        }

    if sub_action == "book":
        return {
            "stage": "booking",
            "message": "Processing your booking request...",
        }

    if result.get("hotel_results"):
        return {
            "stage": "searching",
            "message": "Found hotel options.",
        }

    if result.get("flight_results"):
        return {
            "stage": "searching",
            "message": "Found flight options.",
        }

    return {
        "stage": "responding",
        "message": "Preparing your answer...",
    }

def _build_initial_state(message: str) -> dict:
    recent_pairs = conversation_history_messages[-3:]
    flattened_messages = []

    for user_msg, assistant_msg in recent_pairs:
        flattened_messages.append(user_msg)
        flattened_messages.append(assistant_msg)

    flattened_messages.append(message)

    return {
        "messages": flattened_messages,
        "intent": "",
        "sub_action": "",
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
        "hotel_results": [],
        "flight_results": [],
        "response_text": "",
    }

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}


@app.get("/hotels")
async def list_hotels():
    return get_hotels.invoke({})


@app.get("/flights")
async def list_flights():
    return get_flights.invoke({})


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    initial_state = _build_initial_state(request.message)
    
    try:
        result = graph.invoke(initial_state)

    except Exception as exc:
        print(f"Unexpected chat graph error: {exc}")
        result = {
            "response_text": (
                "Something went wrong while planning your trip. "
                "Please try again."),
                "hotel_results": [],
                "flight_results": [],
        }

    response_text = result.get("response_text", "Something went wrong. Please try again.")

    conversation_history_messages.append((request.message, response_text))

    return ChatResponse(
        response=response_text,
        hotels=result.get("hotel_results", []) or None,
        flights=result.get("flight_results", []) or None,
    )

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    def event_generator():
        try:
            yield _stream_event({
                "type": "activity",
                "stage": "routing",
                "message": "Understanding your request...",
            })

            initial_state = _build_initial_state(request.message)

            yield _stream_event({
                "type": "activity",
                "stage": "routing",
                "message": "Choosing the right travel agent...",
            })

            result = graph.invoke(initial_state)

            activity = _activity_from_result(result)

            yield _stream_event({
                "type": "activity",
                "stage": activity["stage"],
                "message": activity["message"],
            })

            response_text = result.get(
                "response_text",
                "Something went wrong. Please try again.",
            )

            conversation_history_messages.append((request.message, response_text))

            yield _stream_event({
                "type": "message",
                "content": response_text,
                "hotels": result.get("hotel_results", []) or None,
                "flights": result.get("flight_results", []) or None,
            })

            yield _stream_event({"type": "done"})

        except Exception as exc:
            print(f"Unexpected chat stream error: {exc}")
            yield _stream_event({
                "type": "error",
                "message": (
                    "Something went wrong while streaming your trip plan. "
                    "Please try again in a moment."
                ),
            })
            yield _stream_event({"type": "done"})

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
