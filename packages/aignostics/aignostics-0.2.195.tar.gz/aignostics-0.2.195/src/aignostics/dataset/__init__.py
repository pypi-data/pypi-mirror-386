"""Dataset module."""

from importlib.util import find_spec

from aignostics.third_party.idc_index import IDCClient

from ._cli import cli
from ._service import Service

__all__ = [
    "IDCClient",
    "Service",
    "cli",
]

if find_spec("nicegui"):
    from ._gui import PageBuilder

    __all__ += [
        "PageBuilder",
    ]
