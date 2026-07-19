import pytest

import agents.nodes as nodes


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("yes", "confirm"),
        ("confirm", "confirm"),
        ("book it", "confirm"),
        ("go ahead", "confirm"),
        ("cancel", "cancel"),
        ("stop this booking", "cancel"),
        ("don't book it", "cancel"),
        ("never mind", "cancel"),
        ("change my email", "change"),
        ("update the passenger name", "change"),
        ("use a deluxe room instead", "change"),
        (
            "yes, but change my email",
            "change",
        ),
        ("hello", "unknown"),
        ("show me flights", "unknown"),
                (
            "what is the hotel cancellation policy",
            "unknown",
        ),
        (
            "what is the exchange rate",
            "unknown",
        ),
    ],
)
def test_booking_decision_classification(
    message,
    expected,
):
    assert nodes._booking_decision(message) == expected