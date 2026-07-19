import agents.nodes as nodes


HOTEL = {
    "_id": "hotel-1",
    "name": "Test Hotel",
}

FLIGHT = {
    "_id": "flight-1",
    "airline": "Test Airways",
    "flightNumber": "TA100",
    "origin": {"airport": "BKK"},
    "destination": {"airport": "SIN"},
    "flightDate": "2026-08-10",
    "departureTime": "10:00",
    "currency": "USD",
    "price": 200,
}


class ExtractedData:
    def __init__(self, data):
        self.data = data

    def dict(self):
        return self.data


class FixedExtractor:
    def __init__(self, data):
        self.data = data

    def invoke(self, messages):
        return ExtractedData(self.data)


class ToolMustNotRun:
    def invoke(self, payload):
        raise AssertionError(
            "Changed booking must be confirmed again"
        )


def change_state(**overrides):
    state = {
        "messages": [],
        "last_hotel_results": [HOTEL],
        "last_flight_results": [FLIGHT],
        "pending_hotel_booking": None,
        "pending_flight_booking": None,
        "booking_confirmed": False,
    }
    state.update(overrides)
    return state


def test_hotel_change_updates_only_email_and_reconfirms(
    monkeypatch,
):
    pending_hotel = {
        "hotel": HOTEL,
        "details": {
            "hotel_id": "hotel-1",
            "guest_name": "TripWeaver Test",
            "guest_email": "old@example.com",
            "check_in_date": "2026-08-10",
            "check_out_date": "2026-08-12",
            "room_type": "standard",
        },
        "awaiting_confirmation": True,
    }

    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        FixedExtractor(
            {
                "intent": "unknown",
                "sub_action": "general",
                "guest_email": "new@example.com",
            }
        ),
    )
    monkeypatch.setattr(
        nodes,
        "book_hotel",
        ToolMustNotRun(),
    )

    state = change_state(
        messages=[
            "change my email to new@example.com"
        ],
        pending_hotel_booking=pending_hotel,
    )

    routed = nodes.router(state)

    assert routed["intent"] == "hotel"
    assert routed["sub_action"] == "book"
    assert routed["booking_confirmed"] is False
    assert routed["guest_email"] == (
        "new@example.com"
    )

    node_state = {
        **state,
        **routed,
    }
    result = nodes.hotel_node(node_state)

    updated = result["pending_hotel_booking"]

    assert updated["awaiting_confirmation"] is True
    assert updated["details"]["guest_email"] == (
        "new@example.com"
    )
    assert updated["details"]["guest_name"] == (
        "TripWeaver Test"
    )
    assert updated["details"]["room_type"] == (
        "standard"
    )
    assert "new@example.com" in result[
        "response_text"
    ]
    assert "Reply yes to confirm" in result[
        "response_text"
    ]
    assert "cancel to stop" in result[
        "response_text"
    ]


def test_flight_change_updates_only_name_and_reconfirms(
    monkeypatch,
):
    pending_flight = {
        "flight": FLIGHT,
        "details": {
            "flight_id": "flight-1",
            "passenger_name": "Old Name",
            "passenger_email": "test@example.com",
        },
        "awaiting_confirmation": True,
    }

    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        FixedExtractor(
            {
                "intent": "unknown",
                "sub_action": "general",
                "passenger_name": "New Name",
            }
        ),
    )
    monkeypatch.setattr(
        nodes,
        "book_flight",
        ToolMustNotRun(),
    )

    state = change_state(
        messages=[
            "change passenger name to New Name"
        ],
        pending_flight_booking=pending_flight,
    )

    routed = nodes.router(state)

    assert routed["intent"] == "flight"
    assert routed["sub_action"] == "book"
    assert routed["booking_confirmed"] is False
    assert routed["passenger_name"] == "New Name"

    node_state = {
        **state,
        **routed,
    }
    result = nodes.flight_node(node_state)

    updated = result["pending_flight_booking"]

    assert updated["awaiting_confirmation"] is True
    assert updated["details"][
        "passenger_name"
    ] == "New Name"
    assert updated["details"][
        "passenger_email"
    ] == "test@example.com"
    assert "New Name" in result["response_text"]
    assert "Reply yes to confirm" in result[
        "response_text"
    ]
    assert "cancel to stop" in result[
        "response_text"
    ]