"""Boot sequence."""

import os
import ssl
import sys
from pathlib import Path

import certifi
import truststore

from ._log import logging_initialize

# Import third party dependencies.
third_party_dir = Path(__file__).parent.absolute() / ".." / "third_party"
if third_party_dir.is_dir() and str(third_party_dir) not in sys.path:
    sys.path.insert(0, str(third_party_dir))

# Amend library path
if "DYLD_FALLBACK_LIBRARY_PATH" not in os.environ:
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = f"{os.getenv('HOMEBREW_PREFIX', '/opt/homebrew')}/lib/"

from ._constants import __project_name__, __version__  # noqa: E402
from ._log import get_logger  # noqa: E402
from ._process import get_process_info  # noqa: E402

_boot_called = False


def boot(modules_to_instrument: list[str]) -> None:
    """Boot the application.

    Args:
        modules_to_instrument (list): List of modules to be instrumented.
    """
    global _boot_called  # noqa: PLW0603
    if _boot_called:
        return
    _boot_called = True

    _amend_ssl_trust_chain()

    from ._sentry import sentry_initialize  # noqa: PLC0415

    sentry_initialize()

    log_to_logfire = False
    from ._logfire import logfire_initialize  # noqa: PLC0415

    log_to_logfire = logfire_initialize(modules_to_instrument)

    _parse_env_args()
    logging_initialize(log_to_logfire)

    _log_boot_message()


def _parse_env_args() -> None:
    """Parse --env arguments from command line and add to environment if prefix matches.

    - Last but not least removes those args so typer does not complain about them.
    """
    logger = get_logger(__name__)
    logger.debug("_parse_env_args called with sys.argv: %s", sys.argv)

    i = 1  # Start after script name
    to_remove = []
    prefix = f"{__project_name__.upper()}_"

    while i < len(sys.argv):
        current_arg = sys.argv[i]

        # Handle "--env KEY=VALUE" or "-e KEY=VALUE" format (two separate arguments)
        if (current_arg in {"--env", "-e"}) and i + 1 < len(sys.argv):
            key_value = sys.argv[i + 1]
            if "=" in key_value:
                key, value = key_value.split("=", 1)
                if key.startswith(prefix):
                    os.environ[key] = value.strip("\"'")
                to_remove.extend([i, i + 1])
                i += 2
                continue

        i += 1

    # Remove processed arguments from sys.argv in reverse order
    for index in sorted(to_remove, reverse=True):
        del sys.argv[index]


def _amend_ssl_trust_chain() -> None:
    truststore.inject_into_ssl()

    if ssl.get_default_verify_paths().cafile is None and os.environ.get("SSL_CERT_FILE") is None:
        os.environ["SSL_CERT_FILE"] = certifi.where()


def _log_boot_message() -> None:
    """Log boot message with version and process information."""
    logger = get_logger(__name__)
    process_info = get_process_info()
    logger.info(
        "⭐ Booting %s v%s (project root %s, pid %s), parent '%s' (pid %s)",
        __project_name__,
        __version__,
        process_info.project_root,
        process_info.pid,
        process_info.parent.name,
        process_info.parent.pid,
    )
