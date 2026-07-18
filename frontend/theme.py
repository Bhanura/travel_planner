from pathlib import Path

import gradio as gr


FRONTEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = FRONTEND_DIR / "static"
CSS_PATH = STATIC_DIR / "tripweaver.css"

APP_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.orange,
    neutral_hue=gr.themes.colors.slate,
    radius_size=gr.themes.sizes.radius_lg,
)