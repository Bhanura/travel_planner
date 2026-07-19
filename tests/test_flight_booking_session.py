from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

PENDING_FLIGHT_BOOKING = {
    "flight": {
        "_id": "internal-flight-2",
        "airline": "Cathay Pacific",
        "flightNumber": "CA9954",
    },
    "details": {
        "flight_id": "internal-flight-2",
        "passenger_name": "TripWeaver Test",
        "passenger_email": None,
    },
    "awaiting_confirmation": False,
}

class PendingFlightGraph:
    def __init__(self):
        self.received_states = []

    def invoke(self, state):
        self.received_states.append(state)

        if len(self.received_states) == 1:
            return {
                "response_text": (
                    "I still need your passenger email."
                ),
                "hotel_results": [],
                "flight_results": [],
                "pending_flight_booking": (
                    PENDING_FLIGHT_BOOKING
                ),
            }

        return {
            "response_text": "Pending state received.",
            "hotel_results": [],
            "flight_results": [],
        }

def test_chat_reuses_pending_flight_booking(
    monkeypatch,
):
    fake_graph = PendingFlightGraph()

    monkeypatch.setattr(
        main,
        "graph",
        fake_graph,
    )

    session_id = "flight-pending-chat-test"
    main.conversation_sessions.pop(session_id, None)

    first_response = client.post(
        "/chat",
        json={
            "message": (
                "My passenger name is TripWeaver Test"
            ),
            "session_id": session_id,
        },
    )

    second_response = client.post(
        "/chat",
        json={
            "message": (
                "My email is "
                "tripweaver.test@example.com"
            ),
            "session_id": session_id,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    second_state = fake_graph.received_states[1]

    assert (
        second_state["pending_flight_booking"]
        == PENDING_FLIGHT_BOOKING
    )

class PendingFlightStreamingGraph:
    def __init__(self):
        self.received_states = []

    async def astream(
        self,
        state,
        *,
        stream_mode,
        version,
    ):
        self.received_states.append(state)

        assert stream_mode == ["updates", "messages"]
        assert version == "v2"

        if len(self.received_states) == 1:
            update = {
                "response_text": (
                    "I still need your passenger email."
                ),
                "hotel_results": [],
                "flight_results": [],
                "pending_flight_booking": (
                    PENDING_FLIGHT_BOOKING
                ),
            }
        else:
            update = {
                "response_text": (
                    "Pending streaming state received."
                ),
                "hotel_results": [],
                "flight_results": [],
            }

        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "flight_node": update,
            },
        }

def test_stream_reuses_pending_flight_booking(
    monkeypatch,
):
    fake_graph = PendingFlightStreamingGraph()

    monkeypatch.setattr(
        main,
        "graph",
        fake_graph,
    )

    session_id = "flight-pending-stream-test"
    main.conversation_sessions.pop(session_id, None)

    first_response = client.post(
        "/chat/stream",
        json={
            "message": (
                "My passenger name is TripWeaver Test"
            ),
            "session_id": session_id,
        },
    )

    second_response = client.post(
        "/chat/stream",
        json={
            "message": (
                "My email is "
                "tripweaver.test@example.com"
            ),
            "session_id": session_id,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    second_state = fake_graph.received_states[1]

    assert (
        second_state["pending_flight_booking"]
        == PENDING_FLIGHT_BOOKING
    )

class ClearingPendingFlightGraph:
    def __init__(self):
        self.received_states = []

    def invoke(self, state):
        self.received_states.append(state)

        call_number = len(self.received_states)

        if call_number == 1:
            return {
                "response_text": "Pending booking created.",
                "hotel_results": [],
                "flight_results": [],
                "pending_flight_booking": (
                    PENDING_FLIGHT_BOOKING
                ),
            }

        if call_number == 2:
            return {
                "response_text": "Pending booking cleared.",
                "hotel_results": [],
                "flight_results": [],
                "pending_flight_booking": None,
            }

        return {
            "response_text": "Final state inspected.",
            "hotel_results": [],
            "flight_results": [],
        }


def test_chat_can_clear_pending_flight_booking(
    monkeypatch,
):
    fake_graph = ClearingPendingFlightGraph()

    monkeypatch.setattr(
        main,
        "graph",
        fake_graph,
    )

    session_id = "flight-pending-clear-test"
    main.conversation_sessions.pop(session_id, None)

    for message in [
        "Create pending flight booking",
        "Clear pending flight booking",
        "Check pending flight booking",
    ]:
        response = client.post(
            "/chat",
            json={
                "message": message,
                "session_id": session_id,
            },
        )

        assert response.status_code == 200

    assert (
        fake_graph.received_states[1][
            "pending_flight_booking"
        ]
        == PENDING_FLIGHT_BOOKING
    )

    assert (
        fake_graph.received_states[2][
            "pending_flight_booking"
        ]
        is None
    )


class IsolatedFlightSessionGraph:
    def __init__(self):
        self.received_states = []

    def invoke(self, state):
        self.received_states.append(state)

        if len(self.received_states) == 1:
            return {
                "response_text": "Session A pending.",
                "hotel_results": [],
                "flight_results": [],
                "pending_flight_booking": (
                    PENDING_FLIGHT_BOOKING
                ),
            }

        return {
            "response_text": "Session B inspected.",
            "hotel_results": [],
            "flight_results": [],
        }


def test_pending_flight_booking_is_session_isolated(
    monkeypatch,
):
    fake_graph = IsolatedFlightSessionGraph()

    monkeypatch.setattr(
        main,
        "graph",
        fake_graph,
    )

    session_a = "flight-isolation-session-a"
    session_b = "flight-isolation-session-b"

    main.conversation_sessions.pop(session_a, None)
    main.conversation_sessions.pop(session_b, None)

    first_response = client.post(
        "/chat",
        json={
            "message": "Create pending booking",
            "session_id": session_a,
        },
    )

    second_response = client.post(
        "/chat",
        json={
            "message": "Inspect another session",
            "session_id": session_b,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        fake_graph.received_states[1][
            "pending_flight_booking"
        ]
        is None
    )