import agents.nodes as nodes


HOTEL = {
    "_id": "hotel-1",
    "name": "Test Hotel",
    "city": "Bangkok",
    "currency": "USD",
    "pricePerNight": 120,
}


FLIGHT = {
    "_id": "flight-1",
    "airline": "Test Airways",
    "flightNumber": "TA100",
    "origin": {
        "airport": "CMB",
    },
    "destination": {
        "airport": "SIN",
    },
    "flightDate": "2026-08-10",
    "departureTime": "10:00",
    "currency": "USD",
    "price": 200,
}


class ReturningTool:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return self.result


class FailingTool:
    def __init__(self, private_message):
        self.private_message = private_message

    def invoke(self, payload):
        raise RuntimeError(self.private_message)


class ModelResponse:
    def __init__(self, content):
        self.content = content


class GeneralModel:
    def invoke(self, messages):
        return ModelResponse(
            "General travel advice is still available."
        )


def hotel_search_state():
    return {
        "sub_action": "search",
        "city": "Bangkok",
        "check_in": None,
        "check_out": None,
        "last_hotel_results": [],
    }


def flight_search_state():
    return {
        "sub_action": "search",
        "origin": "CMB",
        "destination": "SIN",
        "flight_date": None,
    }


def general_state():
    return {
        "messages": [
            "Give me one packing tip"
        ],
        "sub_action": "general",
        "response_text": "",
    }


def test_empty_hotel_results_are_reported_honestly(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "search_hotel",
        ReturningTool([]),
    )

    result = nodes.hotel_node(
        hotel_search_state()
    )

    assert result["hotel_results"] == []
    assert result["flight_results"] == []
    assert "couldn't find any hotels" in result[
        "response_text"
    ].lower()


def test_empty_flight_results_are_reported_honestly(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "search_flights",
        ReturningTool([]),
    )

    result = nodes.flight_node(
        flight_search_state()
    )

    assert result["hotel_results"] == []
    assert result["flight_results"] == []
    assert "couldn't find flights" in result[
        "response_text"
    ].lower()


def test_hotel_failure_keeps_flight_and_general_agents_usable(
    monkeypatch,
):
    private_error = "private hotel provider failure"

    monkeypatch.setattr(
        nodes,
        "search_hotel",
        FailingTool(private_error),
    )
    monkeypatch.setattr(
        nodes,
        "search_flights",
        ReturningTool([FLIGHT]),
    )
    monkeypatch.setattr(
        nodes,
        "llm",
        GeneralModel(),
    )

    hotel_result = nodes.hotel_node(
        hotel_search_state()
    )
    flight_result = nodes.flight_node(
        flight_search_state()
    )
    general_result = nodes.unknown_node(
        general_state()
    )

    assert "trouble reaching" in hotel_result[
        "response_text"
    ].lower()
    assert private_error not in hotel_result[
        "response_text"
    ]
    assert flight_result["flight_results"] == [
        FLIGHT
    ]
    assert general_result["response_text"] == (
        "General travel advice is still available."
    )


def test_flight_failure_keeps_hotel_and_general_agents_usable(
    monkeypatch,
):
    private_error = "private flight provider failure"

    monkeypatch.setattr(
        nodes,
        "search_flights",
        FailingTool(private_error),
    )
    monkeypatch.setattr(
        nodes,
        "search_hotel",
        ReturningTool([HOTEL]),
    )
    monkeypatch.setattr(
        nodes,
        "llm",
        GeneralModel(),
    )

    flight_result = nodes.flight_node(
        flight_search_state()
    )
    hotel_result = nodes.hotel_node(
        hotel_search_state()
    )
    general_result = nodes.unknown_node(
        general_state()
    )

    assert "trouble reaching" in flight_result[
        "response_text"
    ].lower()
    assert private_error not in flight_result[
        "response_text"
    ]
    assert hotel_result["hotel_results"] == [
        HOTEL
    ]
    assert general_result["response_text"] == (
        "General travel advice is still available."
    )

