# DO NOT EDIT
# Generated from .copier-answers.yml

import sys
from importlib.metadata import PackageNotFoundError, version

from slidge import entrypoint

# import everything for automatic subclasses discovery by slidge core
from . import config, contact, gateway, session

try:
    __version__ = version("slidgnal")
except PackageNotFoundError:
    # package is not installed
    __version__ = "dev"


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--version":
        print("slidgnal version", __version__)
        exit(0)
    entrypoint("slidgnal")


__all__ = (
    "__version__",
    "command",
    "config",
    "contact",
    "gateway",
    "group",
    "main",
    "session",
)
