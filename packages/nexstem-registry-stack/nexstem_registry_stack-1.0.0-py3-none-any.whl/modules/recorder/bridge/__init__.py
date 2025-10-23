"""
Bridge module for Recorder operations.

This module provides the bridge layer for Recorder operations,
handling the CFFI integration with the native C++ library.
"""

from .recorder_bridge import RecorderBridge

__all__ = [
    "RecorderBridge",
]
