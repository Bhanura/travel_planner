from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class SuccessfulGraph:
    def invoke(self, state):
        return {
            "response_text": "I found a suitable hotel.",
            "hotel_results": [
                {
                    "_id": "hotel-1",
                    "name": "Test Hotel",
                }
            ],
            "flight_results": [],
        }


class FailingGraph:
    def invoke(self, state):
        raise RuntimeError("private infrastructure information")


def test_chat_returns_expected_response_schema(monkeypatch):
    monkeypatch.setattr(main, "graph", SuccessfulGraph())

    response = client.post(
        "/chat",
        json={
            "message": "Find a hotel",
            "session_id": "chat-success-test",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "I found a suitable hotel.",
        "hotels": [
            {
                "_id": "hotel-1",
                "name": "Test Hotel",
            }
        ],
        "flights": None,
    }


def test_chat_returns_safe_response_when_graph_fails(monkeypatch):
    monkeypatch.setattr(main, "graph", FailingGraph())

    response = client.post(
        "/chat",
        json={
            "message": "Plan my trip",
            "session_id": "chat-failure-test",
        },
    )

    body = response.json()
    response_text = body["response"]

    assert response.status_code == 200
    assert response_text == (
        "Something went wrong while planning your trip. "
        "Please try again."
    )
    assert "private infrastructure information" not in response_text
    assert "RuntimeError" not in response_text
    assert body["hotels"] is None
    assert body["flights"] is None