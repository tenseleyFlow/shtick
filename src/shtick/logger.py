"""
Logging configuration for shtick
"""

import logging
import sys


def setup_logging(debug: bool = False, name: str = "shtick") -> logging.Logger:
    """
    Set up logging configuration for shtick.

    Args:
        debug: Enable debug logging
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Set level and format based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logger.setLevel(logging.INFO)
        # Simple format for non-debug - just the message
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
