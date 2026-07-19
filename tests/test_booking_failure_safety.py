import agents.nodes as nodes
from streaming_events import (
    activities_from_graph_update,
)


FLIGHT = {
    "_id": "internal-flight-2",
    "airline": "Cathay Pacific",
    "flightNumber": "CA9954",
    "origin": {
        "airport": "BKK",
    },
    "destination": {
        "airport": "SIN",
    },
    "flightDate": "2025-11-15",
    "departureTime": "12:45",
    "currency": "USD",
    "price": 248,
}


PENDING_FLIGHT = {
    "flight": FLIGHT,
    "details": {
        "flight_id": "internal-flight-2",
        "passenger_name": "TripWeaver Test",
        "passenger_email": (
            "tripweaver.test@example.com"
        ),
    },
    "awaiting_confirmation": True,
}


class FailingBookingTool:
    def __init__(self):
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)

        raise RuntimeError(
            "Private simulated provider failure"
        )


def test_failed_flight_booking_preserves_pending_state(
    monkeypatch,
):
    booking_tool = FailingBookingTool()

    monkeypatch.setattr(
        nodes,
        "book_flight",
        booking_tool,
    )

    result = nodes.flight_node(
        {
            "sub_action": "book",
            "flight_id": "internal-flight-2",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
            "last_flight_results": [FLIGHT],
            "pending_flight_booking": (
                PENDING_FLIGHT
            ),
            "booking_confirmed": True,
        }
    )

    assert len(booking_tool.calls) == 1
    assert "trouble reaching" in result[
        "response_text"
    ].lower()
    assert (
        "Private simulated provider failure"
        not in result["response_text"]
    )

    assert result["booking_confirmed"] is False
    assert (
        result["pending_flight_booking"]
        == PENDING_FLIGHT
    )

HOTEL = {
    "_id": "hotel-2",
    "name": "Hyatt BOM 2",
    "city": "Mumbai",
    "currency": "USD",
    "pricePerNight": 237,
}


PENDING_HOTEL = {
    "hotel": HOTEL,
    "details": {
        "hotel_id": "hotel-2",
        "guest_name": "TripWeaver Test",
        "guest_email": (
            "tripweaver.test@example.com"
        ),
        "check_in_date": "2026-08-10",
        "check_out_date": "2026-08-12",
        "room_type": "standard",
    },
    "awaiting_confirmation": True,
}

def test_failed_hotel_booking_preserves_pending_state(
    monkeypatch,
):
    booking_tool = FailingBookingTool()

    monkeypatch.setattr(
        nodes,
        "book_hotel",
        booking_tool,
    )

    result = nodes.hotel_node(
        {
            "sub_action": "book",
            "hotel_id": "hotel-2",
            "guest_name": "TripWeaver Test",
            "guest_email": (
                "tripweaver.test@example.com"
            ),
            "check_in": "2026-08-10",
            "check_out": "2026-08-12",
            "room_type": "standard",
            "last_hotel_results": [HOTEL],
            "pending_hotel_booking": (
                PENDING_HOTEL
            ),
            "booking_confirmed": True,
        }
    )

    assert len(booking_tool.calls) == 1
    assert "trouble reaching" in result[
        "response_text"
    ].lower()
    assert (
        "Private simulated provider failure"
        not in result["response_text"]
    )

    assert result["booking_confirmed"] is False
    assert (
        result["pending_hotel_booking"]
        == PENDING_HOTEL
    )

def test_booking_failures_map_to_error_activities():
    cases = [
        (
            "hotel_node",
            "Hotel Agent",
            (
                "I'm having trouble reaching the "
                "hotel service right now."
            ),
        ),
        (
            "flight_node",
            "Flight Agent",
            (
                "I'm having trouble reaching the "
                "flight service right now."
            ),
        ),
    ]

    for node_name, agent_label, response in cases:
        events = activities_from_graph_update(
            node_name,
            {
                "response_text": response,
            },
        )

        assert events == [
            {
                "type": "activity",
                "stage": "error",
                "message": (
                    f"{agent_label} could not reach "
                    "its travel service."
                ),
            }
        ]