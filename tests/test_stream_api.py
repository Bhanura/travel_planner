import json

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class SuccessfulStreamingGraph:
    def invoke(self, state):
        return {
            "response_text": (
                "Streaming response arrives in multiple "
                "readable chunks for the traveller."
            ),
            "hotel_results": [
                {
                    "_id": "hotel-1",
                    "name": "Stream Hotel",
                }
            ],
            "flight_results": [],
        }


class FailingStreamingGraph:
    def invoke(self, state):
        raise RuntimeError("private streaming infrastructure detail")


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

    assert event_types[:3] == [
        "activity",
        "activity",
        "activity",
    ]
    assert events[0]["stage"] == "routing"
    assert events[1]["stage"] == "routing"
    assert events[2]["stage"] == "searching"
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
        "activity",
        "error",
        "done",
    ]

    error_message = events[2]["message"]

    assert "private streaming infrastructure detail" not in error_message
    assert "RuntimeError" not in error_message