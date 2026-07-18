import os

from .layout import demo
from .theme import APP_THEME, CSS_PATH


def main() -> None:
    port = int(os.environ.get("PORT", "7860"))

    demo.launch(
        css_paths=CSS_PATH,
        theme=APP_THEME,
        footer_links=[],
        server_name="0.0.0.0",
        server_port=port,
    )


if __name__ == "__main__":
    main()