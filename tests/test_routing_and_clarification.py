import pytest

import agents.nodes as nodes


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
            "Missing-input clarification must not call a tool"
        )


def routing_state(message):
    return {
        "messages": [message],
        "last_hotel_results": [],
        "last_flight_results": [],
        "pending_hotel_booking": None,
        "pending_flight_booking": None,
        "booking_confirmed": False,
    }


@pytest.mark.parametrize(
    (
        "message",
        "extracted",
        "expected_route",
    ),
    [
        (
            "Find hotels in Bangkok",
            {
                "intent": "hotel",
                "sub_action": "search",
                "city": "Bangkok",
            },
            "hotel",
        ),
        (
            "Find flights from CMB to SIN",
            {
                "intent": "flight",
                "sub_action": "search",
                "origin": "CMB",
                "destination": "SIN",
            },
            "flight",
        ),
        (
            "What should I pack for Bangkok?",
            {
                "intent": "unknown",
                "sub_action": "general",
            },
            "unknown",
        ),
        (
            "I need something for my trip",
            {
                "intent": "unknown",
                "sub_action": "general",
            },
            "unknown",
        ),
    ],
)
def test_router_dispatches_supported_intents(
    monkeypatch,
    message,
    extracted,
    expected_route,
):
    monkeypatch.setattr(
        nodes,
        "travel_extractor",
        FixedExtractor(extracted),
    )

    routed = nodes.router(
        routing_state(message)
    )

    assert (
        nodes.route_after_extraction(routed)
        == expected_route
    )
    assert routed["intent"] == (
        extracted["intent"]
    )


def test_hotel_search_without_city_asks_for_city(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "search_hotel",
        ToolMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "get_hotels",
        ToolMustNotRun(),
    )

    result = nodes.hotel_node(
        {
            "sub_action": "search",
            "city": None,
            "check_in": None,
            "check_out": None,
            "last_hotel_results": [],
        }
    )

    assert result["hotel_results"] == []
    assert result["flight_results"] == []
    assert "still need your city" in result[
        "response_text"
    ].lower()


@pytest.mark.parametrize(
    (
        "origin",
        "destination",
        "missing_label",
    ),
    [
        (
            "CMB",
            None,
            "destination city or airport",
        ),
        (
            None,
            "SIN",
            "departure city or airport",
        ),
    ],
)
def test_flight_search_asks_for_only_missing_route_field(
    monkeypatch,
    origin,
    destination,
    missing_label,
):
    monkeypatch.setattr(
        nodes,
        "search_flights",
        ToolMustNotRun(),
    )
    monkeypatch.setattr(
        nodes,
        "get_flights",
        ToolMustNotRun(),
    )

    result = nodes.flight_node(
        {
            "sub_action": "search",
            "origin": origin,
            "destination": destination,
            "flight_date": None,
        }
    )

    response = result["response_text"].lower()

    assert result["hotel_results"] == []
    assert result["flight_results"] == []
    assert missing_label in response

