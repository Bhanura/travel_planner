import pytest

import agents.nodes as nodes


HOTEL_PENDING = {
    "hotel": {
        "_id": "hotel-1",
        "name": "Test Hotel",
    },
    "details": {
        "hotel_id": "hotel-1",
        "guest_name": "TripWeaver Test",
    },
    "awaiting_confirmation": True,
}


FLIGHT_PENDING = {
    "flight": {
        "_id": "flight-1",
        "airline": "Test Airways",
        "flightNumber": "TA100",
    },
    "details": {
        "flight_id": "flight-1",
        "passenger_name": "TripWeaver Test",
    },
    "awaiting_confirmation": True,
}


class ExtractorMustNotRun:
    def invoke(self, messages):
        raise AssertionError(
            "Booking control must bypass the LLM"
        )


def control_state(message, **overrides):
    state = {
        "messages": [message],
        "last_hotel_results": [],
        "last_flight_results": [],
        "pending_hotel_booking": None,
        "pending_flight_booking": None,
        "booking_confirmed": False,
    }
    state.update(overrides)
    return state


@pytest.mark.parametrize(
    "message",
    [
        "yes",
        "cancel",
    ],
)
def test_control_without_pending_does_not_use_history(
    monkeypatch,
    message,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    result = nodes.router(
        control_state(message)
    )

    assert result["intent"] == "unknown"
    assert result["sub_action"] == (
        "booking_control"
    )
    assert result["booking_confirmed"] is False
    assert "no pending booking" in result[
        "response_text"
    ].lower()


def test_cancel_collecting_booking_before_confirmation(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    collecting_flight = {
        **FLIGHT_PENDING,
        "awaiting_confirmation": False,
    }

    result = nodes.router(
        control_state(
            "cancel",
            pending_flight_booking=(
                collecting_flight
            ),
        )
    )

    assert result["intent"] == "flight"
    assert result["sub_action"] == "cancel"
    assert (
        result["pending_flight_booking"]
        is None
    )


def test_bare_cancel_with_two_pending_asks_which(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    result = nodes.router(
        control_state(
            "cancel",
            pending_hotel_booking=(
                HOTEL_PENDING
            ),
            pending_flight_booking=(
                FLIGHT_PENDING
            ),
        )
    )

    assert result["intent"] == "unknown"
    assert result["sub_action"] == (
        "booking_control"
    )
    assert "hotel" in result[
        "response_text"
    ].lower()
    assert "flight" in result[
        "response_text"
    ].lower()
    assert (
        result["pending_hotel_booking"]
        == HOTEL_PENDING
    )
    assert (
        result["pending_flight_booking"]
        == FLIGHT_PENDING
    )


@pytest.mark.parametrize(
    (
        "message",
        "cancelled_key",
        "preserved_key",
        "preserved_value",
    ),
    [
        (
            "cancel hotel",
            "pending_hotel_booking",
            "pending_flight_booking",
            FLIGHT_PENDING,
        ),
        (
            "cancel flight",
            "pending_flight_booking",
            "pending_hotel_booking",
            HOTEL_PENDING,
        ),
    ],
)
def test_targeted_cancel_with_two_pending(
    monkeypatch,
    message,
    cancelled_key,
    preserved_key,
    preserved_value,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        ExtractorMustNotRun(),
    )

    result = nodes.router(
        control_state(
            message,
            pending_hotel_booking=(
                HOTEL_PENDING
            ),
            pending_flight_booking=(
                FLIGHT_PENDING
            ),
        )
    )

    assert result["sub_action"] == "cancel"
    assert result[cancelled_key] is None
    assert result[preserved_key] == (
        preserved_value
    )

class LlmMustNotRun:
    def invoke(self, messages):
        raise AssertionError(
            "Booking control response must bypass the LLM"
        )


def test_unknown_node_preserves_booking_control_response(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "llm",
        LlmMustNotRun(),
    )

    expected_response = (
        "There is no pending booking "
        "to confirm or cancel."
    )

    state = control_state("yes")
    state.update(
        {
            "sub_action": "booking_control",
            "response_text": expected_response,
        }
    )

    result = nodes.unknown_node(state)

    assert result["response_text"] == expected_response
    assert result["hotel_results"] == []
    assert result["flight_results"] == []