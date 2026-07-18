import uuid

import gradio as gr

from .handlers import respond
from .presenters import (
    render_progress,
    render_results_panel,
    toggle_results,
)

def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="TripWeaver | AI Travel Planner",
        fill_width=True,
    ) as demo:
        session_id = gr.State(str(uuid.uuid4()))

        results_state = gr.State({
            "hotels": [],
            "flights": [],
            "expanded": False,
        })

        gr.HTML(
            """
            <section class="tw-hero" role="banner">
                <div class="tw-hero__content">
                    <div class="tw-hero__eyebrow">
                        MCP-POWERED MULTI-AGENT TRAVEL PLANNER
                    </div>

                    <h1>
                        Trip<span>Weaver</span>
                    </h1>

                    <p class="tw-hero__description">
                        Discover hotels, explore flights, and plan your next
                        journey through one intelligent travel conversation.
                    </p>

                    <div class="tw-hero__features">
                        <span>✈ Natural flight search</span>
                        <span>🏨 Curated hotel options</span>
                        <span>✓ Human-confirmed bookings</span>
                    </div>

                    <div class="tw-hero__signature">
                        Designed &amp; built by
                        <strong>Bhanura Waduge</strong>
                    </div>
                </div>
            </section>
            """
        )


        with gr.Row():
            with gr.Column(
                scale=4,
                min_width=320,
                elem_classes=["tw-chat-shell"],
            ):
                gr.HTML(
                    """
                    <div class="tw-section-heading">
                        <div>
                            <span class="tw-section-kicker">YOUR JOURNEY STARTS HERE</span>
                            <h2>Where would you like to go?</h2>
                            <p>
                                Ask naturally—TripWeaver will choose the right
                                travel agent for you.
                            </p>
                        </div>
                    </div>
                    """
                )

                with gr.Row(elem_classes=["tw-quick-actions"]):
                    hotel_example = gr.Button(
                        "🏨 Find hotels in Bangkok",
                        elem_classes=["tw-quick-action"],
                    )
                    flight_example = gr.Button(
                        "✈️ Fly from Bangkok to Mumbai",
                        elem_classes=["tw-quick-action"],
                    )
                    inspiration_example = gr.Button(
                        "🌴 Plan a weekend in Singapore",
                        elem_classes=["tw-quick-action"],
                    )

                chatbot = gr.Chatbot(
                    height=350,
                    show_label=False,
                    layout="bubble",
                    placeholder=(
                        "Start with a destination, hotel request, "
                        "flight route, or general travel question."
                    ),
                    feedback_options=None,
                    buttons=["copy"],
                    elem_id="tw-chatbot",
                )

                with gr.Row(elem_classes=["tw-message-row"]):
                    message = gr.Textbox(
                        show_label=False,
                        placeholder=(
                            "Tell me where you want to go, your dates, "
                            "or what you would like to book..."
                        ),
                        lines=2,
                        max_lines=5,
                        scale=8,
                        elem_id="tw-message",
                    )

                    submit = gr.Button(
                        "Plan my trip  →",
                        variant="primary",
                        scale=2,
                        elem_id="tw-send",
                    )

                hotel_example.click(
                    lambda: "Find hotels in Bangkok",
                    outputs=[message],
                )

                flight_example.click(
                    lambda: "Find flights from Bangkok to Mumbai",
                    outputs=[message],
                )

                inspiration_example.click(
                    lambda: "Help me plan a weekend trip to Singapore",
                    outputs=[message],
                )

            with gr.Column(scale=1):
                with gr.Accordion("Agent progress", open=True):
                    progress = gr.HTML(render_progress([]))

                with gr.Accordion("Travel results", open=True):
                    results = gr.HTML(render_results_panel({"hotels": [], "flights": [], "expanded": False}))
                    toggle_results_button = gr.Button("See All / Collapse")

        submit.click(
            respond,
            inputs=[message, chatbot, session_id, results_state],
            outputs=[chatbot, message, progress, results, results_state],
        )
        
        message.submit(
            respond,
            inputs=[message, chatbot, session_id, results_state],
            outputs=[chatbot, message, progress, results, results_state],
        )

        toggle_results_button.click(
            toggle_results,
            inputs=[results_state],
            outputs=[results, results_state],
        )

    return demo

demo = build_demo()
