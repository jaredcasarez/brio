"""
Logging configuration for trax

Provides a centralized logging system with configurable levels and formatters.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


# Log level constants for convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name, typically __name__
        
    Returns:
        Configured logger instance
    """
    # Create logger with hierarchical name under trax
    if name.startswith('trax.'):
        logger_name = name
    else:
        logger_name = f"trax.{name}"
    
    return logging.getLogger(logger_name)


def configure_logging(
    level: int = INFO,
    log_file: Optional[str] = None,
    console: bool = True,
    format_string: Optional[str] = None,
    date_format: str = "%H:%M:%S",
) -> logging.Logger:
    """
    Configure the root trax logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console: Whether to output to console
        format_string: Custom format string for log messages
        date_format: Date/time format string
        
    Returns:
        The configured root logger
    """
    # Get the root trax logger
    root_logger = logging.getLogger("trax")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Default format
    if format_string is None:
        if level == DEBUG:
            format_string = "[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d - %(message)s"
        else:
            format_string = "[%(asctime)s] %(levelname)-8s %(message)s"
    
    formatter = logging.Formatter(format_string, datefmt=date_format)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(log_path, mode='a', encoding='utf-8', maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def set_level(level: int) -> None:
    """
    Set the logging level for all trax loggers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger("trax").setLevel(level)


def enable_debug() -> None:
    """Enable debug level logging."""
    set_level(DEBUG)


def enable_quiet() -> None:
    """Set logging to WARNING level (quiet mode)."""
    set_level(WARNING)


# Module-level logger shortcuts for common use cases
class LogLevel:
    """Enumeration of log levels with descriptive names."""
    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL
    
    # Aliases
    WARN = WARNING
    FATAL = CRITICAL
    VERBOSE = DEBUG
    QUIET = WARNING


# Initialize default logging on import
_default_logger = configure_logging(level=INFO)


# Create a convenience logger for the main brio module
logger = get_logger("main")
