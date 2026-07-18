import os
import logging

import gradio as gr
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from entity import ChatRequest, ChatResponse
from agents.tools import get_hotels, get_flights
from agents.graph import graph
from frontend import (
    APP_THEME,
    CSS_PATH,
    STATIC_DIR,
    demo as frontend_demo,
)
from streaming_events import (
    activities_from_graph_update,
    encode_stream_event,
    iter_text_chunks,
)

conversation_sessions = {}

app = FastAPI()

app.mount(
    "/assets",
    StaticFiles(directory=STATIC_DIR),
    name="assets",
)

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

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()

if not allowed_origins_raw:
    raise RuntimeError(
        "ALLOWED_ORIGINS is required but was not configured."
    )

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in allowed_origins_raw.split(",")
    if origin.strip()
]

if not ALLOWED_ORIGINS:
    raise RuntimeError(
        "ALLOWED_ORIGINS must contain at least one origin."
    )

if "*" in ALLOWED_ORIGINS:
    raise RuntimeError(
        "ALLOWED_ORIGINS must use explicit origins; wildcard '*' is not allowed."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
async def root():
    return {
        "service": "TripWeaver API",
        "status": "running",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    dependencies = {
        "llm_configured": bool(
            os.getenv("OPENAI_API_KEY", "").strip()
        ),
        "hotel_provider_configured": bool(
            os.getenv("HOTEL_PROVIDER_BASE_URL", "").strip()
        ),
        "flight_provider_configured": bool(
            os.getenv("FLIGHT_PROVIDER_BASE_URL", "").strip()
        ),
    }

    status = (
        "healthy"
        if all(dependencies.values())
        else "degraded"
    )

    return {
        "status": status,
        "service": "tripweaver-backend",
        "dependencies": dependencies,
    }

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
    async def event_generator():
        try:
            yield encode_stream_event({
                "type": "activity",
                "stage": "routing",
                "message": "Understanding your request...",
            })

            initial_state = _build_initial_state(
                request.message,
                request.session_id,
            )

            result = initial_state.copy()

            async for stream_part in graph.astream(
                initial_state,
                stream_mode="updates",
                version="v2",
            ):
                if stream_part.get("type") != "updates":
                    continue

                node_updates = stream_part.get(
                    "data",
                    {},
                )

                if not isinstance(node_updates, dict):
                    continue

                for node_name, node_update in node_updates.items():
                    if not isinstance(node_update, dict):
                        continue

                    result.update(node_update)

                    activity_events = (
                        activities_from_graph_update(
                            node_name,
                            node_update,
                        )
                    )

                    for activity_event in activity_events:
                        yield encode_stream_event(
                            activity_event
                        )

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

            for text_chunk in iter_text_chunks(response_text):
                yield encode_stream_event({
                    "type": "delta",
                    "content": text_chunk,
                })

            yield encode_stream_event({
                "type": "message",
                "content": response_text,
                "hotels": result.get("hotel_results", []) or None,
                "flights": result.get("flight_results", []) or None,
            })

            yield encode_stream_event({"type": "done"})

        except Exception:
            logger.exception("Unexpected chat stream error")
            yield encode_stream_event({
                "type": "error",
                "message": (
                    "Something went wrong while streaming your trip plan. "
                    "Please try again in a moment."
                ),
            })
            yield encode_stream_event({"type": "done"})

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
    )

app = gr.mount_gradio_app(
    app,
    frontend_demo,
    path="/app",
    theme=APP_THEME,
    css_paths=CSS_PATH,
    footer_links=[],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
