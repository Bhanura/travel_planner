import json

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk

import main
from streaming_events import activities_from_graph_update


client = TestClient(main.app)


class SuccessfulStreamingGraph:
    async def astream(
        self,
        state,
        *,
        stream_mode,
        version,
    ):
        assert stream_mode == ["updates", "messages"]
        assert version == "v2"

        hotel_results = [
            {
                "_id": "hotel-1",
                "name": "Stream Hotel",
            }
        ]

        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "router": {
                    "intent": "hotel",
                    "sub_action": "search",
                }
            },
        }
        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "hotel_node": {
                    "hotel_results": hotel_results,
                    "flight_results": [],
                }
            },
        }
        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "generate_response": {
                    "response_text": (
                        "Streaming response arrives in multiple "
                        "readable chunks for the traveller."
                    ),
                }
            },
        }


class GeneralAnswerStreamingGraph:
    async def astream(
        self,
        state,
        *,
        stream_mode,
        version,
    ):
        assert stream_mode == ["updates", "messages"]
        assert version == "v2"

        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "router": {
                    "intent": "unknown",
                    "sub_action": "general",
                }
            },
        }
        yield {
            "type": "messages",
            "ns": (),
            "data": (
                {
                    "event": "content-block-delta",
                    "index": 0,
                    "delta": {
                        "type": "text-delta",
                        "text": "private router output",
                    },
                },
                {"langgraph_node": "router"},
            ),
        }
        yield {
            "type": "messages",
            "ns": (),
            "data": (
                AIMessageChunk(content="Pack "),
                {"langgraph_node": "unknown_node"},
            ),
        }
        yield {
            "type": "messages",
            "ns": (),
            "data": (
                {
                    "event": "content-block-delta",
                    "index": 0,
                    "delta": {
                        "type": "text-delta",
                        "text": "light.",
                    },
                },
                {"langgraph_node": "unknown_node"},
            ),
        }
        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "unknown_node": {
                    "hotel_results": [],
                    "flight_results": [],
                    "response_text": "Pack light.",
                }
            },
        }
        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "generate_response": {
                    "response_text": "Pack light.",
                }
            },
        }


class FailingStreamingGraph:
    async def astream(
        self,
        state,
        *,
        stream_mode,
        version,
    ):
        if state:
            raise RuntimeError(
                "private streaming infrastructure detail"
            )

        yield {}


def parse_events(response):
    return [
        json.loads(line)
        for line in response.text.splitlines()
        if line.strip()
    ]


def test_stream_returns_events_in_expected_order(monkeypatch):
    monkeypatch.setattr(
        main,
        "graph",
        SuccessfulStreamingGraph(),
    )

    response = client.post(
        "/chat/stream",
        json={
            "message": "Find a hotel",
            "session_id": "stream-success-test",
        },
    )

    events = parse_events(response)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/x-ndjson"
    )
    event_types = [
        event["type"]
        for event in events
    ]
    delta_events = [
        event
        for event in events
        if event["type"] == "delta"
    ]

    message_index = event_types.index("message")
    done_index = event_types.index("done")

    activity_events = [
        event
        for event in events
        if event["type"] == "activity"
    ]

    assert [
        event["stage"]
        for event in activity_events
    ] == [
        "routing",
        "routing",
        "routing",
        "searching",
        "responding",
    ]
    assert [
        event["message"]
        for event in activity_events
    ] == [
        "Understanding your request...",
        "Search request identified.",
        "Hotel Agent selected.",
        "1 matching hotel options found.",
        "Preparing your final answer.",
    ]
    assert len(delta_events) >= 2
    assert all(
        index < message_index
        for index, event_type in enumerate(event_types)
        if event_type == "delta"
    )
    assert message_index < done_index

    streamed_text = "".join(
        event["content"]
        for event in delta_events
    )
    final_event = events[message_index]

    assert streamed_text == final_event["content"]
    assert final_event["hotels"][0]["_id"] == "hotel-1"


def test_model_tokens_stream_before_final_node_update(monkeypatch):
    monkeypatch.setattr(
        main,
        "graph",
        GeneralAnswerStreamingGraph(),
    )

    response = client.post(
        "/chat/stream",
        json={
            "message": "How should I pack?",
            "session_id": "live-model-stream-test",
        },
    )

    events = parse_events(response)
    event_types = [event["type"] for event in events]
    delta_events = [
        event
        for event in events
        if event["type"] == "delta"
    ]
    public_output = response.text

    assert response.status_code == 200
    assert [event["content"] for event in delta_events] == [
        "Pack ",
        "light.",
    ]
    assert "private router output" not in public_output

    prepared_index = next(
        index
        for index, event in enumerate(events)
        if event.get("message")
        == "General Travel Agent prepared a response."
    )
    last_delta_index = max(
        index
        for index, event_type in enumerate(event_types)
        if event_type == "delta"
    )
    message_index = event_types.index("message")

    assert last_delta_index < prepared_index < message_index
    assert events[message_index]["content"] == "Pack light."
    assert event_types[-1] == "done"


def test_stream_returns_safe_error_then_done(monkeypatch):
    monkeypatch.setattr(
        main,
        "graph",
        FailingStreamingGraph(),
    )

    response = client.post(
        "/chat/stream",
        json={
            "message": "Plan my trip",
            "session_id": "stream-failure-test",
        },
    )

    events = parse_events(response)

    assert response.status_code == 200
    assert [event["type"] for event in events] == [
        "activity",
        "error",
        "done",
    ]

    error_message = events[1]["message"]

    assert "private streaming infrastructure detail" not in error_message
    assert "RuntimeError" not in error_message

def test_activity_mapper_does_not_expose_private_state():
    events = activities_from_graph_update(
        "router",
        {
            "intent": "hotel",
            "sub_action": "search",
            "guest_email": "private@example.com",
            "system_prompt": "private routing instructions",
        },
    )

    public_output = json.dumps(events)

    assert "private@example.com" not in public_output
    assert "private routing instructions" not in public_output
    assert [event["message"] for event in events] == [
        "Search request identified.",
        "Hotel Agent selected.",
    ]
