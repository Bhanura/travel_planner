import json

from fastapi.testclient import TestClient

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
        assert stream_mode == "updates"
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
