"""Utilities module."""

from ._cli import prepare_cli
from ._console import console
from ._constants import (
    __author_email__,
    __author_name__,
    __base__url__,
    __build_number__,
    __documentation__url__,
    __env__,
    __env_file__,
    __is_development_mode__,
    __is_running_in_container__,
    __is_running_in_read_only_environment__,
    __project_name__,
    __project_path__,
    __repository_url__,
    __version__,
    __version_full__,
)
from ._di import load_modules, locate_implementations, locate_subclasses
from ._fs import get_user_data_directory, open_user_data_directory, sanitize_path, sanitize_path_component
from ._health import Health
from ._log import LogSettings, get_logger
from ._process import SUBPROCESS_CREATION_FLAGS, ProcessInfo, get_process_info
from ._service import BaseService
from ._settings import UNHIDE_SENSITIVE_INFO, OpaqueSettings, load_settings, strip_to_none_before_validator
from ._user_agent import user_agent
from .boot import boot

__all__ = [
    "SUBPROCESS_CREATION_FLAGS",
    "UNHIDE_SENSITIVE_INFO",
    "BaseService",
    "Health",
    "LogSettings",
    "OpaqueSettings",
    "ProcessInfo",
    "__author_email__",
    "__author_name__",
    "__base__url__",
    "__build_number__",
    "__documentation__url__",
    "__env__",
    "__env_file__",
    "__is_development_mode__",
    "__is_running_in_container__",
    "__is_running_in_read_only_environment__",
    "__project_name__",
    "__project_path__",
    "__repository_url__",
    "__version__",
    "__version_full__",
    "boot",
    "console",
    "get_logger",
    "get_process_info",
    "get_user_data_directory",
    "load_modules",
    "load_settings",
    "locate_implementations",
    "locate_subclasses",
    "open_user_data_directory",
    "prepare_cli",
    "sanitize_path",
    "sanitize_path_component",
    "strip_to_none_before_validator",
    "user_agent",
]

from importlib.util import find_spec

if find_spec("logfire"):
    from ._logfire import LogfireSettings, logfire_initialize

    __all__ += ["LogfireSettings", "logfire_initialize"]

if find_spec("sentry"):
    from ._sentry import SentrySettings

    __all__ += ["SentrySettings"]

if find_spec("nicegui"):
    from ._gui import BasePageBuilder, GUILocalFilePicker, gui_register_pages, gui_run

    __all__ += ["BasePageBuilder", "GUILocalFilePicker", "gui_register_pages", "gui_run"]

if find_spec("marimo"):
    from ._notebook import create_marimo_app

    __all__ += [
        "create_marimo_app",
    ]
