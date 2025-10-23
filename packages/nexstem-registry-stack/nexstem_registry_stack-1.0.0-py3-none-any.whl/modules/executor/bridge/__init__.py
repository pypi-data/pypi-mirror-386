"""
Executor Bridge module.

This module provides the bridge layer for Executor operations,
handling FFI communication with the native executor bridge library.
"""

from .executor_bridge import ExecutorBridge

__all__ = [
    'ExecutorBridge'
]