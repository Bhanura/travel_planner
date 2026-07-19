from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


PENDING_HOTEL_BOOKING = {
    "hotel": {
        "_id": "hotel-1",
        "name": "Test Hotel",
    },
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


class CancelledHotelGraph:
    def invoke(self, state):
        assert (
            state["pending_hotel_booking"]
            == PENDING_HOTEL_BOOKING
        )

        return {
            "intent": "hotel",
            "sub_action": "cancel",
            "response_text": (
                "Your hotel booking request "
                "was cancelled."
            ),
            "hotel_results": [],
            "flight_results": [],
            "pending_hotel_booking": None,
            "booking_confirmed": False,
        }


class CancelledHotelStreamingGraph:
    async def astream(
        self,
        state,
        *,
        stream_mode,
        version,
    ):
        assert (
            state["pending_hotel_booking"]
            == PENDING_HOTEL_BOOKING
        )
        assert stream_mode == ["updates", "messages"]
        assert version == "v2"

        yield {
            "type": "updates",
            "ns": (),
            "data": {
                "hotel_node": {
                    "intent": "hotel",
                    "sub_action": "cancel",
                    "response_text": (
                        "Your hotel booking request "
                        "was cancelled."
                    ),
                    "hotel_results": [],
                    "flight_results": [],
                    "pending_hotel_booking": None,
                    "booking_confirmed": False,
                }
            },
        }


def prepare_hotel_session(session_id):
    session = main._empty_session()
    session["pending_hotel_booking"] = (
        PENDING_HOTEL_BOOKING
    )
    main.conversation_sessions[session_id] = session


def test_chat_clears_cancelled_hotel_session(
    monkeypatch,
):
    session_id = "hotel-cancel-chat-test"
    prepare_hotel_session(session_id)

    monkeypatch.setattr(
        main,
        "graph",
        CancelledHotelGraph(),
    )

    response = client.post(
        "/chat",
        json={
            "message": "cancel",
            "session_id": session_id,
        },
    )

    assert response.status_code == 200
    assert (
        main.conversation_sessions[session_id][
            "pending_hotel_booking"
        ]
        is None
    )


def test_stream_clears_cancelled_hotel_session(
    monkeypatch,
):
    session_id = "hotel-cancel-stream-test"
    prepare_hotel_session(session_id)

    monkeypatch.setattr(
        main,
        "graph",
        CancelledHotelStreamingGraph(),
    )

    response = client.post(
        "/chat/stream",
        json={
            "message": "cancel",
            "session_id": session_id,
        },
    )

    assert response.status_code == 200
    assert (
        main.conversation_sessions[session_id][
            "pending_hotel_booking"
        ]
        is None
    )