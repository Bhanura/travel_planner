import json
import re
from collections.abc import Iterator


def encode_stream_event(event: dict) -> str:
    """Encode one event as a single NDJSON record."""
    return json.dumps(
        event,
        ensure_ascii=False,
    ) + "\n"


def iter_text_chunks(
    text: str,
    max_chars: int = 48,
) -> Iterator[str]:
    """
    Split text into readable chunks while preserving
    the original text exactly when chunks are joined.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    pieces = re.findall(r"\S+\s*|\s+", text)
    buffer = ""

    for piece in pieces:
        if buffer and len(buffer) + len(piece) > max_chars:
            yield buffer
            buffer = piece
        else:
            buffer += piece

    if buffer:
        yield buffer


def text_from_message_chunk(message: object) -> str:
    """Return public text from a LangGraph message stream item."""
    if isinstance(message, dict):
        if message.get("event") != "content-block-delta":
            return ""

        delta = message.get("delta", {})

        if (
            isinstance(delta, dict)
            and delta.get("type") == "text-delta"
            and isinstance(delta.get("text"), str)
        ):
            return delta["text"]

        return ""

    content = getattr(message, "content", "")

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


AGENT_LABELS = {
    "hotel": "Hotel Agent",
    "flight": "Flight Agent",
    "unknown": "General Travel Agent",
}

ACTION_LABELS = {
    "search": "Search request",
    "list_all": "Listing request",
    "book": "Booking request",
    "general": "General travel request",
}


def activities_from_graph_update(
    node_name: str,
    update: dict,
) -> list[dict]:
    """
    Convert a LangGraph node update into traveller-safe
    Agent Journey activity events.

    Never return the raw graph state, prompts, personal
    details, or exception information.
    """
    if not isinstance(update, dict):
        return []

    if node_name == "router":
        intent = str(
            update.get("intent", "unknown")
        )
        sub_action = str(
            update.get("sub_action", "general")
        )

        agent_label = AGENT_LABELS.get(
            intent,
            "General Travel Agent",
        )
        action_label = ACTION_LABELS.get(
            sub_action,
            "Travel request",
        )

        return [
            {
                "type": "activity",
                "stage": "routing",
                "message": f"{action_label} identified.",
            },
            {
                "type": "activity",
                "stage": "routing",
                "message": f"{agent_label} selected.",
            },
        ]

    if node_name == "hotel_node":
        hotel_results = (
            update.get("hotel_results")
            or []
        )

        if hotel_results:
            return [{
                "type": "activity",
                "stage": "searching",
                "message": (
                    f"{len(hotel_results)} matching "
                    "hotel options found."
                ),
            }]

        return [
            _agent_response_activity(
                "Hotel Agent",
                update,
            )
        ]

    if node_name == "flight_node":
        flight_results = (
            update.get("flight_results")
            or []
        )

        if flight_results:
            return [{
                "type": "activity",
                "stage": "searching",
                "message": (
                    f"{len(flight_results)} matching "
                    "flight options found."
                ),
            }]

        return [
            _agent_response_activity(
                "Flight Agent",
                update,
            )
        ]

    if node_name == "unknown_node":
        return [{
            "type": "activity",
            "stage": "responding",
            "message": (
                "General Travel Agent prepared a response."
            ),
        }]

    if node_name == "generate_response":
        return [{
            "type": "activity",
            "stage": "responding",
            "message": "Preparing your final answer.",
        }]

    return []


def _agent_response_activity(
    agent_label: str,
    update: dict,
) -> dict:
    """
    Describe an agent outcome without exposing the
    response body or internal state.
    """
    response_text = str(
        update.get("response_text", "")
    )

    if "I still need" in response_text:
        return {
            "type": "activity",
            "stage": "clarifying",
            "message": (
                f"{agent_label} needs more details."
            ),
        }

    if "trouble reaching" in response_text:
        return {
            "type": "activity",
            "stage": "error",
            "message": (
                f"{agent_label} could not reach "
                "its travel service."
            ),
        }

    return {
        "type": "activity",
        "stage": "responding",
        "message": f"{agent_label} completed its step.",
    }