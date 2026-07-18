import os
import pytest

os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["HOTEL_PROVIDER_BASE_URL"] = "https://hotel-provider.test"
os.environ["FLIGHT_PROVIDER_BASE_URL"] = "https://flight-provider.test"
os.environ["ALLOWED_ORIGINS"] = "http://frontend.test"
os.environ["LOG_LEVEL"] = "WARNING"

@pytest.fixture(autouse=True)
def clear_conversation_sessions():
    import main

    main.conversation_sessions.clear()
    yield
    main.conversation_sessions.clear()