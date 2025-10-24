"""Logging configuration and utilities."""

import contextlib
import logging as python_logging
import os
from logging import Filter as LogggingFilter
from logging import Handler
from pathlib import Path
from typing import Annotated, Literal

import click
import platformdirs
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.logging import RichHandler

from ._constants import __env_file__, __is_running_in_read_only_environment__, __project_name__
from ._settings import load_settings


def get_logger(name: str | None) -> python_logging.Logger:
    """
    Get a logger instance with the given name or project name as default.

    Args:
        name(str): The name for the logger. If None, uses project name.

    Returns:
        Logger: Configured logger instance.
    """
    if (name is None) or (name == __project_name__):
        return python_logging.getLogger(__project_name__)
    return python_logging.getLogger(f"{__project_name__}.{name}")


def _validate_file_name(file_name: str | None) -> str | None:
    """Validate the file_name is valid and the file writeable.

    - Checks file_name does not yet exist or is a file
    - If not yet existing, checks it can be created
    - If existing file, checks file is writeable

    Args:
        file_name: The file name of the log file

    Returns:
        str | None: The validated file name

    Raises:
        ValueError: If file name is not valid or the file not writeable
    """
    if file_name is None:
        return file_name

    file_path = Path(file_name)
    if file_path.exists():
        if file_path.is_dir():
            message = f"File name {file_path.absolute()} exists but is a directory"
            raise ValueError(message)
        if not os.access(file_path, os.W_OK):
            if file_path.exists():
                message = f"File {file_path.absolute()} is not writable"
                raise ValueError(message)
            return file_name  # This was a race condition, file was deleted in the meantime
    else:
        try:
            file_path.touch(exist_ok=True)
        except OSError as e:
            message = f"File {file_path.absolute()} cannot be created: {e}"
            raise ValueError(message) from e

        with contextlib.suppress(OSError):  # Parallel execution e.g. in tests can create race
            file_path.unlink()

    return file_name


class LogSettings(BaseSettings):
    """Settings for configuring logging behavior."""

    model_config = SettingsConfigDict(
        env_prefix=f"{__project_name__.upper()}_LOG_",
        extra="ignore",
        env_file=__env_file__,
        env_file_encoding="utf-8",
    )

    level: Annotated[
        Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        Field(description="Logging level", default="INFO"),
    ]
    file_enabled: Annotated[
        bool,
        Field(description="Enable logging to file", default=False),
    ]
    file_name: Annotated[
        str,
        Field(
            description="Name of the log file",
            default="/dev/stdout"
            if __is_running_in_read_only_environment__
            else platformdirs.user_data_dir(__project_name__) + f"/{__project_name__}.log",
        ),
    ]
    console_enabled: Annotated[
        bool,
        Field(description="Enable logging to console", default=False),
    ]

    @field_validator("file_name")
    @classmethod
    def validate_file_name_when_enabled(cls, file_name: str, info: ValidationInfo) -> str:
        """
        Validate file_name only when file_enabled is True.

        Args:
            file_name: The file name to validate.
            info: Validation info containing other field values.

        Returns:
            str: The validated file name.
        """
        # Check if file_enabled is True in the provided data
        if info.data.get("file_enabled", False):
            _validate_file_name(file_name)
        return file_name


class CustomFilter(LogggingFilter):
    """Filter to exclude specific dependencies or their messages from logging."""

    def filter(self, record: python_logging.LogRecord) -> bool:  # noqa: PLR6301
        """
        Filter out log records from specific dependencies.

        Args:
            record: The log record to filter.

        Returns:
            bool: True if the record should be logged, False otherwise.
        """
        excluded_dependencies: set[str] | dict[str, str] = {"bla"}
        if record.name in excluded_dependencies:
            return False
        return not (record.name == "dotenv.main" and record.getMessage().endswith("key doesn't exist."))


def logging_initialize(log_to_logfire: bool = False) -> None:
    """Initialize logging configuration."""
    log_filter = CustomFilter()

    handlers: list[Handler] = []

    settings = load_settings(LogSettings)

    if settings.file_enabled:
        file_handler = python_logging.FileHandler(settings.file_name)
        file_formatter = python_logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] [%(process)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(log_filter)
        handlers.append(file_handler)

    if settings.console_enabled:
        rich_handler = RichHandler(
            console=Console(stderr=True),
            markup=True,
            rich_tracebacks=True,
            tracebacks_suppress=[click],
            show_time=True,
            omit_repeated_times=True,
            show_path=True,
            show_level=True,
            enable_link_path=True,
        )
        rich_handler.addFilter(log_filter)
        handlers.append(rich_handler)

    if log_to_logfire:
        from importlib.util import find_spec  # noqa: PLC0415

        if find_spec("logfire"):
            import logfire  # noqa: PLC0415

            logfire_handler = logfire.LogfireLoggingHandler()
            logfire_handler.addFilter(log_filter)
            handlers.append(logfire_handler)

    if not handlers:
        handlers = [python_logging.NullHandler()]
    python_logging.basicConfig(
        level=settings.level,
        format=r"\[%(name)s] [%(process)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
