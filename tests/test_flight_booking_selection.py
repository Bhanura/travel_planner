import pytest

from agents.nodes import _resolve_flight_selection


FLIGHTS = [
    {
        "_id": "internal-flight-1",
        "airline": "Japan Airlines",
        "flightNumber": "JA7622",
    },
    {
        "_id": "internal-flight-2",
        "airline": "Cathay Pacific",
        "flightNumber": "CA9954",
    },
    {
        "_id": "internal-flight-3",
        "airline": "Thai Airways",
        "flightNumber": "TH5780",
    },
]


@pytest.mark.parametrize(
    "candidate",
    [
        "2",
        "option 2",
        "flight 2",
        "second",
        "second option",
        "second flight",
        "internal-flight-2",
        "CA9954",
        "ca9954",
        "Cathay Pacific CA9954",
    ],
)
def test_resolve_flight_selection_accepts_natural_choices(
    candidate,
):
    selected = _resolve_flight_selection(
        candidate,
        FLIGHTS,
    )

    assert selected is FLIGHTS[1]
    assert selected["_id"] == "internal-flight-2"


@pytest.mark.parametrize(
    "candidate",
    [
        None,
        "",
        "option 0",
        "option 99",
        "CA99",
        "Cathay Pacific",
        "unknown flight",
    ],
)
def test_resolve_flight_selection_rejects_invalid_choices(
    candidate,
):
    selected = _resolve_flight_selection(
        candidate,
        FLIGHTS,
    )

    assert selected is None


def test_resolve_flight_selection_requires_stored_results():
    assert _resolve_flight_selection(
        "option 2",
        [],
    ) is None