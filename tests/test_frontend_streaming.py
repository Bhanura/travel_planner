import frontend.handlers as handlers


def test_frontend_appends_delta_chunks_without_activity_overwrite(monkeypatch):
    def fake_stream_chat_api(message, session_id):
        yield {
            "type": "activity",
            "stage": "routing",
            "message": "Choosing the right agent...",
        }
        yield {"type": "delta", "content": "Pack "}
        yield {
            "type": "activity",
            "stage": "responding",
            "message": "Preparing your final answer.",
        }
        yield {"type": "delta", "content": "light."}
        yield {
            "type": "message",
            "content": "Pack light.",
            "hotels": None,
            "flights": None,
        }
        yield {"type": "done"}

    monkeypatch.setattr(
        handlers,
        "stream_chat_api",
        fake_stream_chat_api,
    )

    visible_assistant_text = []

    for output in handlers.respond(
        "How should I pack?",
        [],
        "frontend-delta-test",
        {
            "hotels": [],
            "flights": [],
            "expanded": False,
        },
    ):
        history = output[0]
        visible_assistant_text.append(
            history[-1]["content"]
        )

    assert "Pack " in visible_assistant_text
    assert "Choosing the right agent..." not in visible_assistant_text
    assert "Preparing your final answer." not in visible_assistant_text
    assert visible_assistant_text.count("Pack ") == 2
    assert visible_assistant_text[-2:] == [
        "Pack light.",
        "Pack light.",
    ]
