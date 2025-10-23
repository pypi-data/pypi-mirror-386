"""Themed rich console."""

from rich.console import Console
from rich.theme import Theme

console = Console(
    theme=Theme({
        "logging.level.info": "purple4",
        "debug": "light_cyan3",
        "success": "green",
        "info": "purple4",
        "warning": "yellow1",
        "error": "red1",
    }),
)
