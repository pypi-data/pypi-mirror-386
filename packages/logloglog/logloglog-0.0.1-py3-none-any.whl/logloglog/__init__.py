"""LogLogLog - Efficient scrollback indexing for large log files."""

import logging
import sys
from importlib.metadata import version, PackageNotFoundError


from .logloglog import LogLogLog
from .widthview import WidthView

try:
    __version__ = version("logloglog")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0+dev"

__all__ = ["LogLogLog", "WidthView", "configure_logging"]


# Configure logging for LogLogLog
def configure_logging(level=logging.INFO):
    """Configure logging for LogLogLog."""
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # Configure logloglog loggers
    for logger_name in ["logloglog.logloglog", "logloglog.wraptree", "logloglog.index"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        logger.addHandler(handler)


# Auto-configure with DEBUG level for performance monitoring
configure_logging(logging.DEBUG)
