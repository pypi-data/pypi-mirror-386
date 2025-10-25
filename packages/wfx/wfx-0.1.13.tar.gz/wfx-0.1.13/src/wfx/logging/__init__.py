"""Backwards compatibility module for wfx.logging.

This module provides backwards compatibility for code that imports from wfx.logging.
All functionality has been moved to wfx.log.
"""

# Re-export everything from wfx.log for backwards compatibility
from wfx.log.logger import configure, logger

# Maintain the same __all__ exports
__all__ = ["configure", "logger"]
