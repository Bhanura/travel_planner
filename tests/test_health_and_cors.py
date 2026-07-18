from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_root_returns_service_metadata():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "TripWeaver API",
        "status": "running",
        "health": "/health",
        "docs": "/docs",
    }


def test_health_reports_configured_dependencies():
    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "healthy"
    assert body["service"] == "tripweaver-backend"
    assert all(body["dependencies"].values())


def test_health_reports_degraded_dependency(monkeypatch):
    monkeypatch.setenv("HOTEL_PROVIDER_BASE_URL", " ")

    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "degraded"
    assert body["dependencies"]["hotel_provider_configured"] is False


def test_cors_allows_only_configured_origin():
    allowed = client.options(
        "/health",
        headers={
            "Origin": "http://frontend.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    denied = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert (
        allowed.headers["access-control-allow-origin"]
        == "http://frontend.test"
    )
    assert allowed.headers.get("access-control-allow-credentials") is None

    assert denied.status_code == 400
    assert denied.headers.get("access-control-allow-origin") is None


def test_gradio_frontend_is_mounted():
    response = client.get("/app/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "TripWeaver" in response.text
