"""
trax - A Panda3D-based track layout designer
"""

from logging import config

from .sandbox import SandboxApp
from .constants import Colors
from .assets import Assets
from .utils import todecimal, rgba
from .logging import get_logger, configure_logging, set_level, LogLevel

# Tools are available via trax.tools
from . import tools

__all__ =  [
    "SandboxApp",
    "sandbox",
    "Colors",
    "Assets",
    "todecimal",
    "rgba",
    "get_logger",
    "configure_logging",
    "set_level",
    "LogLevel",
    "tools",
]
configure_logging(level=LogLevel.INFO, console=True)  # Set default logging level to INFO
