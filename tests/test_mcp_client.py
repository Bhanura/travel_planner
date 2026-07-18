import pytest

from agents.mcp_client import MCPToolError, _server_environment


@pytest.mark.parametrize(
    ("server", "required_variable", "excluded_variable"),
    [
        (
            "hotel",
            "HOTEL_PROVIDER_BASE_URL",
            "FLIGHT_PROVIDER_BASE_URL",
        ),
        (
            "flight",
            "FLIGHT_PROVIDER_BASE_URL",
            "HOTEL_PROVIDER_BASE_URL",
        ),
    ],
)
def test_mcp_environment_uses_least_privilege(
    monkeypatch,
    server,
    required_variable,
    excluded_variable,
):
    monkeypatch.setenv(
        "HOTEL_PROVIDER_BASE_URL",
        "https://hotel-provider.test",
    )
    monkeypatch.setenv(
        "FLIGHT_PROVIDER_BASE_URL",
        "https://flight-provider.test",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-mcp")

    environment = _server_environment(server)

    assert environment[required_variable]
    assert excluded_variable not in environment
    assert "OPENAI_API_KEY" not in environment


@pytest.mark.parametrize(
    ("server", "required_variable"),
    [
        ("hotel", "HOTEL_PROVIDER_BASE_URL"),
        ("flight", "FLIGHT_PROVIDER_BASE_URL"),
    ],
)
def test_mcp_environment_requires_provider_configuration(
    monkeypatch,
    server,
    required_variable,
):
    monkeypatch.delenv(required_variable, raising=False)

    with pytest.raises(MCPToolError, match=required_variable):
        _server_environment(server)