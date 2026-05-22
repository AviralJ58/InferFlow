"""
Structured logging setup for InferFlow services.

Provides a consistent logging configuration across all services.
Future: integrate with OpenTelemetry for distributed tracing.
"""

import logging
import sys


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging for a service.

    Args:
        service_name: Name of the service (used as logger name and in log format).
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
