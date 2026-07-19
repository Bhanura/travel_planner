import agents.nodes as nodes


HOTEL = {
    "_id": "hotel-1",
    "name": "Test Hotel",
}

FLIGHT = {
    "_id": "flight-1",
    "airline": "Test Airways",
    "flightNumber": "TA100",
}


class ExtractorMustNotRun:
    def invoke(self, messages):
        raise AssertionError(
            "Confirmation must bypass the LLM extractor"
        )


def confirmation_state(**overrides):
    state = {
        "messages": ["yes"],
        "last_hotel_results": [HOTEL],
        "last_flight_results": [FLIGHT],
        "pending_hotel_booking": None,
        "pending_flight_booking": None,
    }
    state.update(overrides)
    return state


def test_hotel_confirmation_routes_without_llm(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    pending_hotel = {
        "hotel": HOTEL,
        "details": {
            "hotel_id": "hotel-1",
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

    result = nodes.router(
        confirmation_state(
            pending_hotel_booking=pending_hotel,
        )
    )

    assert result["intent"] == "hotel"
    assert result["sub_action"] == "book"
    assert result["booking_confirmed"] is True
    assert result["hotel_id"] == "hotel-1"
    assert result["guest_name"] == "TripWeaver Test"


def test_flight_confirmation_routes_without_llm(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    pending_flight = {
        "flight": FLIGHT,
        "details": {
            "flight_id": "flight-1",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
        },
        "awaiting_confirmation": True,
    }

    result = nodes.router(
        confirmation_state(
            pending_flight_booking=pending_flight,
        )
    )

    assert result["intent"] == "flight"
    assert result["sub_action"] == "book"
    assert result["booking_confirmed"] is True
    assert result["flight_id"] == "flight-1"
    assert result["passenger_name"] == (
        "TripWeaver Test"
    )

class RecordingTool:
    def __init__(self, result):
        self.calls = []
        self.result = result

    def invoke(self, payload):
        self.calls.append(payload)
        return self.result


def test_confirmed_hotel_calls_hotel_tool_once(
    monkeypatch,
):
    hotel_tool = RecordingTool(
        {
            "message": "Hotel booking confirmed.",
        }
    )

    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "book_hotel",
        hotel_tool,
    )

    pending_hotel = {
        "hotel": HOTEL,
        "details": {
            "hotel_id": "hotel-1",
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

    confirmed_state = nodes.router(
        confirmation_state(
            pending_hotel_booking=pending_hotel,
        )
    )

    result = nodes.hotel_node(confirmed_state)

    assert hotel_tool.calls == [
        {
            "hotel_id": "hotel-1",
            "guest_name": "TripWeaver Test",
            "guest_email": (
                "tripweaver.test@example.com"
            ),
            "check_in_date": "2026-08-10",
            "check_out_date": "2026-08-12",
            "room_type": "standard",
        }
    ]
    assert "confirmed" in result[
        "response_text"
    ].lower()


def test_confirmed_flight_calls_flight_tool_once(
    monkeypatch,
):
    flight_tool = RecordingTool(
        {
            "message": "Flight booking confirmed.",
        }
    )

    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "book_flight",
        flight_tool,
    )

    pending_flight = {
        "flight": FLIGHT,
        "details": {
            "flight_id": "flight-1",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
        },
        "awaiting_confirmation": True,
    }

    confirmed_state = nodes.router(
        confirmation_state(
            pending_flight_booking=pending_flight,
        )
    )

    result = nodes.flight_node(confirmed_state)

    assert flight_tool.calls == [
        {
            "flight_id": "flight-1",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
        }
    ]
    assert "confirmed" in result[
        "response_text"
    ].lower()

class ToolMustNotRun:
    def invoke(self, payload):
        raise AssertionError(
            "Booking tool must not run during cancellation"
        )


def test_hotel_cancellation_clears_pending_without_tool(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "book_hotel",
        ToolMustNotRun(),
    )

    pending_hotel = {
        "hotel": HOTEL,
        "details": {
            "hotel_id": "hotel-1",
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

    state = confirmation_state(
        messages=["cancel"],
        pending_hotel_booking=pending_hotel,
    )

    routed_state = nodes.router(state)

    assert routed_state["intent"] == "hotel"
    assert routed_state["sub_action"] == "cancel"
    assert (
        routed_state["pending_hotel_booking"]
        is None
    )

    result = nodes.hotel_node(routed_state)

    assert result["pending_hotel_booking"] is None
    assert "cancelled" in result[
        "response_text"
    ].lower()


def test_flight_cancellation_clears_pending_without_tool(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "book_flight",
        ToolMustNotRun(),
    )

    pending_flight = {
        "flight": FLIGHT,
        "details": {
            "flight_id": "flight-1",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
        },
        "awaiting_confirmation": True,
    }

    state = confirmation_state(
        messages=["cancel"],
        pending_flight_booking=pending_flight,
    )

    routed_state = nodes.router(state)

    assert routed_state["intent"] == "flight"
    assert routed_state["sub_action"] == "cancel"
    assert (
        routed_state["pending_flight_booking"]
        is None
    )

    result = nodes.flight_node(routed_state)

    assert result["pending_flight_booking"] is None
    assert "cancelled" in result[
        "response_text"
    ].lower()