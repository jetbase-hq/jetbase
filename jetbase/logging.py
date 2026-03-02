"""
Logging configuration for Jetbase CLI.

Provides centralized logging setup with automatic TTY detection
for switching between human-readable and JSON output formats.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for CI/CD and log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-formatted string representation of the log record.
        """
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        for key in ("migration", "version", "filename"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry)


def is_interactive() -> bool:
    """
    Check if running in an interactive terminal.

    Returns:
        True if stdout is a TTY or if JETBASE_FORCE_INTERACTIVE is set
        to "true", False otherwise.
    """
    if os.environ.get("JETBASE_FORCE_INTERACTIVE", "").lower() == "true":
        return True
    return sys.stdout.isatty()


def configure_logging(
    level: str = "INFO",
    json_output: bool | None = None,
) -> None:
    """
    Configure logging for jetbase CLI.

    Args:
        level: The minimum log level to display (DEBUG, INFO, WARNING, ERROR).
            Defaults to "INFO".
        json_output: If True, output JSON logs. If False, output plain text.
            If None, auto-detect based on TTY. Defaults to None.

    Returns:
        None: Configures the jetbase logger as a side effect.
    """
    logger.handlers.clear()

    # Set the log level
    log_level: int = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Determine output format
    use_json: bool = json_output if json_output is not None else not is_interactive()

    handler: logging.StreamHandler[Any] = logging.StreamHandler(sys.stderr)

    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        # Simple format for interactive use
        handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


# Module-level logger instance
logger: logging.Logger = logging.getLogger("jetbase")

# Ensure logging is configured on import
if not logger.handlers:
    configure_logging()
