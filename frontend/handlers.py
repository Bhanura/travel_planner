from .api_client import (
    FrontendAPIError,
    call_chat_api,
    stream_chat_api,
)
from .presenters import (
    format_chat_response,
    render_progress,
    render_results_panel,
)

def respond(message, history, session_id, results_state):
    if history is None:
        history = []

    if not message.strip():
        yield history, "", render_progress([]), render_results_panel(results_state), results_state
        return

    progress_events = [
        {"stage": "starting", "message": "Starting request..."}
    ]

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": "Starting..."},
    ]

    yield history, "", render_progress(progress_events), render_results_panel(results_state), results_state

    try:
        for event in stream_chat_api(message, session_id):
            event_type = event.get("type")

            if event_type == "activity":
                activity = {
                    "stage": event.get("stage", "working"),
                    "message": event.get("message", "Working..."),
                }

                if progress_events[-1] != activity:
                    progress_events.append(activity)

                history[-1]["content"] = activity["message"]
                yield history, "", render_progress(progress_events), render_results_panel(results_state), results_state

            elif event_type == "message":
                final_message = event.get("content", "No response returned.")
                history[-1]["content"] = final_message
                results_state = {
                    "hotels": event.get("hotels") or [],
                    "flights": event.get("flights") or [],
                    "expanded": False,
                }
                yield history, "", render_progress(progress_events, done=True), render_results_panel(results_state), results_state

            elif event_type == "error":
                error_message = event.get(
                    "message",
                    "Something went wrong. Please try again.",
                )
                progress_events.append({
                    "stage": "error",
                    "message": error_message,
                })
                history[-1]["content"] = error_message
                yield history, "", render_progress(progress_events, error=True), render_results_panel(results_state), results_state

            elif event_type == "done":
                break

    except Exception:
        try:
            fallback_data = call_chat_api(
                message,
                session_id,
            )
            fallback_message = format_chat_response(
                fallback_data
            )
        except FrontendAPIError:
            error_message = (
                "I’m unable to reach the travel service right now. "
                "Please try again in a moment."
            )

            progress_events.append({
                "stage": "error",
                "message": error_message,
            })

            history[-1]["content"] = error_message

            yield (
                history,
                "",
                render_progress(
                    progress_events,
                    error=True,
                ),
                render_results_panel(results_state),
                results_state,
            )
            return

        progress_events.append({
            "stage": "fallback",
            "message": (
                "Live streaming was interrupted, "
                "so TripWeaver used the normal chat response."
            ),
        })

        history[-1]["content"] = fallback_message

        yield (
            history,
            "",
            render_progress(
                progress_events,
                done=True,
            ),
            render_results_panel(results_state),
            results_state,
        )
