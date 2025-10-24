"""Notebook service running Marimo."""

import atexit
import re
import sys
from subprocess import PIPE, STDOUT, Popen
from threading import Event, Thread
from typing import Any

from aignostics.constants import NOTEBOOK_DEFAULT
from aignostics.utils import SUBPROCESS_CREATION_FLAGS, BaseService, Health, get_logger, get_user_data_directory

logger = get_logger(__name__)

MARIMO_SERVER_STARTUP_TIMEOUT = 60


class _Runner:
    """Runner class of the Marimo module."""

    _marimo_server: Popen[str] | None = None
    _monitor_thread: Thread | None = None
    _output: str = ""
    _server_url: str | None = None
    _server_ready: Event = Event()
    _started = False

    def __init__(self) -> None:
        atexit.register(self.stop)

    def health(self) -> Health:
        """Determine health of hello service.

        Returns:
            Health: The health of the service.
        """
        if not self._started:
            return Health(status=Health.Code.UP)
        return Health(
            status=Health.Code.UP,
            components={
                "marimo_server": Health(
                    status=Health.Code.UP if self.is_marimo_server_running() else Health.Code.DOWN,
                    reason=None if self.is_marimo_server_running() else "Marimo server is not running.",
                ),
                "monitor_thread": Health(
                    status=Health.Code.UP if self.is_monitor_thread_alive() else Health.Code.DOWN,
                    reason=None if self.is_monitor_thread_alive() else "Monitor thread is not running.",
                ),
            },
        )

    def start(self, timeout: int = MARIMO_SERVER_STARTUP_TIMEOUT) -> str:
        """Start the Marimo server.

        Args:
            timeout (int): Maximum time to wait for the server to start and URL to be detected.

        Returns:
            str: The URL of the started Marimo server.

        Raises:
            RuntimeError: If the Marimo server fails to start or if the URL isn't detected within given timeout.
        """
        logger.debug("Checking if Marimo server is running...")
        self._started = True
        if self.is_marimo_server_running():
            logger.warning("Marimo server is already running.")
            if self._server_url is not None:
                return self._server_url

            message = "Server is running but URL is not set - this is unexpected."
            logger.error(message)
            raise RuntimeError(message)

        directory = get_user_data_directory("notebooks")
        notebook_path = directory / "notebook.py"
        if not notebook_path.exists():
            logger.debug("Copying notebook to user data directory '%s'...", notebook_path)
            notebook_path.write_bytes(NOTEBOOK_DEFAULT.read_bytes())

        # Reset server state
        self._server_url = None
        self._server_ready.clear()

        logger.debug("Starting Marimo server with notebook at '%s'...", notebook_path)

        if getattr(sys, "frozen", False):
            self._marimo_server = Popen(  # noqa: S603
                [
                    sys.executable,
                    "--run-module",
                    "marimo",
                    "edit",
                    "--headless",
                    "--skip-update-check",
                    "--no-sandbox",
                    "--no-token",
                    str(notebook_path.resolve()),
                ],
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=SUBPROCESS_CREATION_FLAGS,
            )
        else:
            self._marimo_server = Popen(  # noqa: S603
                [
                    sys.executable,
                    "-m",
                    "marimo",
                    "edit",
                    "--headless",
                    "--skip-update-check",
                    "--no-sandbox",
                    "--no-token",
                    str(notebook_path.resolve()),
                ],
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=SUBPROCESS_CREATION_FLAGS,
            )

        # Start a thread to monitor the subprocess output
        self._monitor_thread = Thread(target=self._capture_output, args=(self._marimo_server,), daemon=True)
        self._monitor_thread.start()

        # Wait up to timeout seconds for the server URL to be detected
        if not self._server_ready.wait(timeout=timeout):
            self.stop()  # Kill the process if it didn't start properly
            message = f"Marimo server didn't start within '{timeout}' seconds (URL not detected)."
            logger.error(message)
            raise RuntimeError(message)

        # At this point, self._server_url should be set by thread
        if self._server_url is None:
            self.stop()
            message = "Server URL was not set despite server ready event being triggered."
            logger.error(message)
            raise RuntimeError(message)

        message = f"Marimo server started successfully with URL '{self._server_url}'."  # type: ignore[unreachable]
        logger.info(message)
        return self._server_url

    def _capture_output(self, process: Popen[str]) -> None:
        """Capture stdout of the subprocess and detect when server is ready.

        Args:
            process (Popen): The subprocess to capture stdout from.
        """
        captured_line = ""
        url_pattern = re.compile(r"URL:\s+((?:http|https)://[^\s]{1,100})")

        if process.stdout is None:
            logger.warning("Cannot capture stdout")
            return

        # Buffer for collecting output
        self._output = ""

        while process.poll() is None:
            char = process.stdout.read(1)
            if not char:  # End of stream
                break

            self._output += char
            captured_line += char

            if char == "\n":
                logger.debug(captured_line.rstrip())
                url_match = url_pattern.search(captured_line)
                if url_match:
                    self._server_url = url_match.group(1)
                    logger.info("Found URL: '%s'", self._server_url)
                    self._server_ready.set()

                captured_line = ""

        logger.debug("Marimo server process completed.")

    def is_marimo_server_running(self) -> bool:
        """Check if the marimo server is running.

        Returns:
            bool: True if the server is running, False otherwise.
        """
        return self._marimo_server is not None and self._marimo_server.poll() is None

    def is_monitor_thread_alive(self) -> bool:
        """Check if the monitor thread is running.

        Returns:
            bool: True if the thread is running, False otherwise.
        """
        return self._monitor_thread is not None and self._monitor_thread.is_alive()

    def stop(self) -> None:
        """Stop the Marimo server."""
        if self._marimo_server is not None:
            logger.debug("Stopping Marimo server...")
            self._marimo_server.terminate()
            self._marimo_server.wait(2)
            if self._marimo_server.returncode is None:
                logger.debug("Marimo server did not terminate in time, killing it...")
                self._marimo_server.kill()
            self._marimo_server = None
            logger.info("Marimo server stopped.")
        else:
            logger.debug("Marimo server is not running.")
        if self._monitor_thread is not None:
            self._monitor_thread.join()
            self._monitor_thread = None
            logger.info("Monitor thread stopped.")
        else:
            logger.debug("Monitor thread is not running.")
        logger.info("Service stopped.")


# Singleton instance of Runner
runner: _Runner | None = None


# Lazy init the runner
def _get_runner() -> _Runner:
    """Get the singleton runner.

    Returns:
        Service: The service instance.
    """
    global runner  # noqa: PLW0603
    if runner is None:
        runner = _Runner()
    return runner


# Facade to the Marimo runner
class Service(BaseService):
    """Service of the Marimo module."""

    def info(self, mask_secrets: bool = True) -> dict[str, Any]:  # noqa: ARG002, PLR6301
        """Determine info of this service.

        Args:
            mask_secrets (bool): Whether to mask sensitive information in the output.

        Returns:
            dict[str,Any]: The info of this service.
        """
        return {}

    def health(self) -> Health:  # noqa: PLR6301
        """Determine health of hello service.

        Returns:
            Health: The health of the service.
        """
        return _get_runner().health()

    def start(self) -> str:  # noqa: PLR6301
        """Start the Marimo server.

        Returns:
            str: The URL of the started Marimo server.

        Raises:
            RuntimeError: If the Marimo server fails to start or if the URL isn't detected within 10 seconds.
        """
        return _get_runner().start()

    def is_marimo_server_running(self) -> bool:  # noqa: PLR6301
        """Check if the marimo server is running.

        Returns:
            bool: True if the server is running, False otherwise.
        """
        return _get_runner().is_marimo_server_running()

    def is_monitor_thread_alive(self) -> bool:  # noqa: PLR6301
        """Check if the monitor thread is running.

        Returns:
            bool: True if the thread is running, False otherwise.
        """
        return _get_runner().is_monitor_thread_alive()

    def stop(self) -> None:  # noqa: PLR6301
        """Stop the Marimo server."""
        return _get_runner().stop()
