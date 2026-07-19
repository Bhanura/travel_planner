from frontend.presenters import format_test_transcript


def test_format_test_transcript_contains_visible_chat_only():
    history = [
        {
            "role": "user",
            "content": [
                {
                    "text": "Book option 2",
                    "type": "text",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "text": (
                        "I still need passenger "
                        "name and email."
                    ),
                    "type": "text",
                }
            ],
        },
        {
            "role": "system",
            "content": "private system instructions",
        },
        {
            "role": "user",
            "content": "My name is TripWeaver Test",
        },
    ]

    transcript = format_test_transcript(history)

    assert "USER:\nBook option 2" in transcript
    assert (
        "ASSISTANT:\n"
        "I still need passenger name and email."
        in transcript
    )
    assert "USER:\nMy name is TripWeaver Test" in transcript
    assert "private system instructions" not in transcript
    assert "'type': 'text'" not in transcript
    assert "[{" not in transcript