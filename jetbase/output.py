"""
Output utilities for Jetbase CLI.

Provides helpers for outputting styled messages using Rich.
"""

from rich.console import Console

# Module-level console for rich output
console: Console = Console()


def print_message(message: str, style: str | None = None) -> None:
    """
    Print a message to the console with optional Rich styling.

    Args:
        message: The message to print.
        style: Optional Rich style (e.g., "green", "yellow", "red").

    Returns:
        None: Prints to stdout as a side effect.
    """
    if style:
        console.print(f"[{style}]{message}[/{style}]")
    else:
        console.print(message)
