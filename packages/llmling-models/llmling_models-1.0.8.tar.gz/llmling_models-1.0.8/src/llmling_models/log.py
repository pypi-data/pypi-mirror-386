"""Logging configuration for llmling_models."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: The name of the logger, will be prefixed with 'llmling_agent.'

    Returns:
        A logger instance
    """
    return logging.getLogger(f"llmling_models.{name}")
