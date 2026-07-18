import json

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class SuccessfulStreamingGraph:
    def invoke(self, state):
        return {
            "response_text": "Streaming response",
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
    assert [event["type"] for event in events] == [
        "activity",
        "activity",
        "activity",
        "message",
        "done",
    ]
    assert events[0]["stage"] == "routing"
    assert events[1]["stage"] == "routing"
    assert events[2]["stage"] == "searching"
    assert events[3]["content"] == "Streaming response"
    assert events[3]["hotels"][0]["_id"] == "hotel-1"


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