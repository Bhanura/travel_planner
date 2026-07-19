import agents.nodes as nodes


FLIGHTS = [
    {
        "_id": "internal-flight-1",
        "airline": "Japan Airlines",
        "flightNumber": "JA7622",
        "origin": {"airport": "BKK"},
        "destination": {"airport": "SIN"},
        "flightDate": "2025-11-15",
        "departureTime": "06:30",
        "currency": "USD",
        "price": 273,
    },
    {
        "_id": "internal-flight-2",
        "airline": "Cathay Pacific",
        "flightNumber": "CA9954",
        "origin": {"airport": "BKK"},
        "destination": {"airport": "SIN"},
        "flightDate": "2025-11-15",
        "departureTime": "12:45",
        "currency": "USD",
        "price": 248,
    },
]


class BookingMustNotRun:
    def invoke(self, payload):
        raise AssertionError(
            "Flight booking must not run before confirmation"
        )


def booking_state(**overrides):
    state = {
        "sub_action": "book",
        "flight_id": "option 2",
        "passenger_name": None,
        "passenger_email": None,
        "last_flight_results": FLIGHTS,
        "pending_flight_booking": None,
        "booking_confirmed": False,
    }
    state.update(overrides)
    return state


def test_natural_selection_stores_real_flight_id(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "book_flight",
        BookingMustNotRun(),
    )

    result = nodes.flight_node(booking_state())
    pending = result["pending_flight_booking"]

    assert pending["flight"] is FLIGHTS[1]
    assert (
        pending["details"]["flight_id"]
        == "internal-flight-2"
    )
    assert "passenger name" in result["response_text"]
    assert "passenger email" in result["response_text"]


def test_pending_selection_collects_only_missing_email(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "book_flight",
        BookingMustNotRun(),
    )

    pending = {
        "flight": FLIGHTS[1],
        "details": {
            "flight_id": "internal-flight-2",
            "passenger_name": None,
            "passenger_email": None,
        },
        "awaiting_confirmation": False,
    }

    result = nodes.flight_node(
        booking_state(
            flight_id=None,
            passenger_name="TripWeaver Test",
            pending_flight_booking=pending,
        )
    )

    assert "passenger email" in result["response_text"]
    assert "passenger name" not in result["response_text"]
    assert (
        result["pending_flight_booking"]["details"][
            "passenger_name"
        ]
        == "TripWeaver Test"
    )


def test_complete_details_stop_at_confirmation(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "book_flight",
        BookingMustNotRun(),
    )

    result = nodes.flight_node(
        booking_state(
            passenger_name="TripWeaver Test",
            passenger_email="tripweaver.test@example.com",
        )
    )

    pending = result["pending_flight_booking"]
    response = result["response_text"]

    assert pending["awaiting_confirmation"] is True
    assert "Cathay Pacific CA9954" in response
    assert "BKK to SIN" in response
    assert "TripWeaver Test" in response
    assert "tripweaver.test@example.com" in response
    assert "Reply yes to confirm" in response


def test_invalid_new_selection_does_not_reuse_pending_flight(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "book_flight",
        BookingMustNotRun(),
    )

    pending = {
        "flight": FLIGHTS[0],
        "details": {
            "flight_id": "internal-flight-1",
            "passenger_name": "TripWeaver Test",
            "passenger_email": None,
        },
        "awaiting_confirmation": False,
    }

    result = nodes.flight_node(
        booking_state(
            flight_id="option 99",
            pending_flight_booking=pending,
        )
    )

    assert result["pending_flight_booking"] is None
    assert "choose a valid flight" in result["response_text"]