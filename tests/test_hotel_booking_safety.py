import agents.nodes as nodes


HOTEL = {
    "_id": "hotel-1",
    "name": "Test Hotel",
    "city": "Bangkok",
    "currency": "USD",
    "pricePerNight": 120,
}


class BookingMustNotRun:
    def invoke(self, payload):
        raise AssertionError(
            "Hotel booking must wait for explicit confirmation"
        )


def test_complete_hotel_details_stop_at_confirmation(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "book_hotel",
        BookingMustNotRun(),
    )

    result = nodes.hotel_node(
        {
            "sub_action": "book",
            "hotel_id": "hotel-1",
            "guest_name": "TripWeaver Test",
            "guest_email": (
                "tripweaver.test@example.com"
            ),
            "check_in": "2026-08-10",
            "check_out": "2026-08-12",
            "room_type": "standard",
            "last_hotel_results": [HOTEL],
            "pending_hotel_booking": None,
            "booking_confirmed": False,
        }
    )

    pending = result["pending_hotel_booking"]
    response = result["response_text"]

    assert pending["hotel"] == HOTEL
    assert pending["awaiting_confirmation"] is True
    assert pending["details"] == {
        "hotel_id": "hotel-1",
        "guest_name": "TripWeaver Test",
        "guest_email": (
            "tripweaver.test@example.com"
        ),
        "check_in_date": "2026-08-10",
        "check_out_date": "2026-08-12",
        "room_type": "standard",
    }
    assert "Please confirm this hotel booking" in response
    assert "Reply yes to confirm" in response

