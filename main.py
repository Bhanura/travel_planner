import json
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from entity import ChatRequest, ChatResponse
from agents.tools import get_hotels, get_flights
from agents.graph import graph

conversation_sessions = {}

app = FastAPI()

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=numeric_log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(numeric_log_level)

def _empty_session() -> dict:
    return {
        "messages": [],
        "last_hotel_results": [],
        "last_flight_results": [],
        "pending_hotel_booking": None,
        "pending_flight_booking": None,
    }

def _get_session(session_id: str | None) -> dict:
    safe_session_id = session_id or "default"

    if safe_session_id not in conversation_sessions:
        conversation_sessions[safe_session_id] = _empty_session()

    return conversation_sessions[safe_session_id]

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

def _build_initial_state(message: str, session_id: str | None) -> dict:
    session = _get_session(session_id)
    recent_pairs = session["messages"][-3:]
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
        "last_hotel_results": session["last_hotel_results"],
        "last_flight_results": session["last_flight_results"],
        "pending_hotel_booking": session["pending_hotel_booking"],
        "pending_flight_booking": session["pending_flight_booking"],
        "booking_confirmed": False,
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

    initial_state = _build_initial_state(request.message, request.session_id)

    try:
        result = graph.invoke(initial_state)

    except Exception:
        logger.exception("Unexpected chat graph error")
        result = {
            "response_text": (
                "Something went wrong while planning your trip. "
                "Please try again."),
                "hotel_results": [],
                "flight_results": [],
        }

    response_text = result.get("response_text", "Something went wrong. Please try again.")

    session = _get_session(request.session_id)
    session["messages"].append((request.message, response_text))
    hotel_results = result.get("hotel_results") or []
    flight_results = result.get("flight_results") or []

    if hotel_results:
        session["last_hotel_results"] = hotel_results

    if flight_results:
        session["last_flight_results"] = flight_results

    logger.debug(
        "Stored hotel results: %d",
        len(session["last_hotel_results"]),
    )
    logger.debug(
        "Stored flight results: %d",
        len(session["last_flight_results"]),
    )

    if result.get("pending_hotel_booking") is not None:
        session["pending_hotel_booking"] = result.get("pending_hotel_booking")
        logger.debug("Stored pending hotel booking state")

    if result.get("booking_confirmed"):
        session["pending_hotel_booking"] = None
        logger.debug("Cleared pending hotel booking state")

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

            initial_state = _build_initial_state(request.message, request.session_id)

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

            session = _get_session(request.session_id)
            session["messages"].append((request.message, response_text))
            hotel_results = result.get("hotel_results") or []
            flight_results = result.get("flight_results") or []

            if hotel_results:
                session["last_hotel_results"] = hotel_results

            if flight_results:
                session["last_flight_results"] = flight_results

            logger.debug(
                "Stored hotel results during stream: %d",
                len(session["last_hotel_results"]),
            )
            logger.debug(
                "Stored flight results during stream: %d",
                len(session["last_flight_results"]),
            )

            if result.get("pending_hotel_booking") is not None:
                session["pending_hotel_booking"] = result.get("pending_hotel_booking")
                logger.debug("Stored pending hotel booking state during stream")

            if result.get("booking_confirmed"):
                session["pending_hotel_booking"] = None
                logger.debug("Cleared pending hotel booking state during stream")
            yield _stream_event({
                "type": "message",
                "content": response_text,
                "hotels": result.get("hotel_results", []) or None,
                "flights": result.get("flight_results", []) or None,
            })

            yield _stream_event({"type": "done"})

        except Exception:
            logger.exception("Unexpected chat stream error")
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
