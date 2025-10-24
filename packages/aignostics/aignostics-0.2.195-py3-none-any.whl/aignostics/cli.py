"""CLI (Command Line Interface) of Aignostics Python SDK."""

import sys
from importlib.util import find_spec
from pathlib import Path

import typer

from .constants import NOTEBOOK_DEFAULT
from .utils import (
    __is_running_in_container__,
    __version__,
    console,
    get_logger,
    prepare_cli,
)

logger = get_logger(__name__)

cli = typer.Typer(
    help="Command Line Interface (CLI) of Aignostics Python SDK providing access to Aignostics Platform.",
)

if find_spec("nicegui") and find_spec("webview") and not __is_running_in_container__:

    @cli.command()
    def launchpad() -> None:
        """Open Aignostics Launchpad, the graphical user interface of the Aignostics Platform."""
        from .utils import gui_run  # noqa: PLC0415

        gui_run(native=True, with_api=False, title="Aignostics Launchpad", icon="🔬")


if find_spec("marimo"):
    from typing import Annotated

    from .utils import create_marimo_app

    @cli.command()
    def notebook(
        host: Annotated[str, typer.Option(help="Host to bind the server to")] = "127.0.0.1",
        port: Annotated[int, typer.Option(help="Port to bind the server to")] = 8001,
        notebook: Annotated[
            Path,
            typer.Argument(
                help="Path to the notebook file to run. If not provided, a default notebook will be used.",
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
            ),
        ] = NOTEBOOK_DEFAULT,
        override_if_exists: Annotated[
            bool,
            typer.Option(
                help="Override the notebook in the user data directory if it already exists.",
            ),
        ] = False,
    ) -> None:
        """Run Python notebook server based on Marimo."""
        import uvicorn  # noqa: PLC0415

        console.print(f"Starting Python notebook server at http://{host}:{port}")
        uvicorn.run(create_marimo_app(notebook=notebook, override_if_exists=override_if_exists), host=host, port=port)


prepare_cli(cli, f"🔬 Aignostics Python SDK v{__version__} - built with love in Berlin 🐻")


if __name__ == "__main__":  # pragma: no cover
    try:
        cli()
    except Exception as e:  # noqa: BLE001
        message = f"An error occurred while running the CLI: {e!s}"
        logger.critical(message)
        console.print(message, style="error")
        sys.exit(1)
