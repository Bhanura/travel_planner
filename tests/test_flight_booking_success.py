import agents.nodes as nodes


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


def test_flight_success_message_includes_booking_details():
    provider_result = {
        "booking": {
            "status": "confirmed",
            "bookingReference": "FLT-ABC123",
        }
    }

    message = nodes._flight_booking_success_message(
        provider_result,
        FLIGHT,
    )

    assert "Flight booking confirmed" in message
    assert "Cathay Pacific CA9954" in message
    assert "BKK to SIN" in message
    assert "2025-11-15" in message
    assert "12:45" in message
    assert "USD 248" in message
    assert "FLT-ABC123" in message

class RecordingBookingTool:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return self.result


def test_confirmed_flight_uses_rich_success_message(
    monkeypatch,
):
    booking_tool = RecordingBookingTool(
        {
            "booking": {
                "status": "confirmed",
                "bookingReference": "FLT-ABC123",
            }
        }
    )

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
            "pending_flight_booking": {
                "flight": FLIGHT,
                "details": {
                    "flight_id": (
                        "internal-flight-2"
                    ),
                    "passenger_name": (
                        "TripWeaver Test"
                    ),
                    "passenger_email": (
                        "tripweaver.test@example.com"
                    ),
                },
                "awaiting_confirmation": True,
            },
            "booking_confirmed": True,
        }
    )

    assert booking_tool.calls == [
        {
            "flight_id": "internal-flight-2",
            "passenger_name": "TripWeaver Test",
            "passenger_email": (
                "tripweaver.test@example.com"
            ),
        }
    ]

    response = result["response_text"]

    assert "Flight booking confirmed" in response
    assert "Cathay Pacific CA9954" in response
    assert "BKK to SIN" in response
    assert "USD 248" in response
    assert "FLT-ABC123" in response

def test_flight_success_without_reference_stays_rich():
    provider_result = {
        "message": "Flight booking completed.",
    }

    message = nodes._flight_booking_success_message(
        provider_result,
        FLIGHT,
    )

    assert "Flight booking confirmed" in message
    assert "Cathay Pacific CA9954" in message
    assert "BKK to SIN" in message
    assert "2025-11-15" in message
    assert "12:45" in message
    assert "USD 248" in message
    assert "Booking reference:" not in message