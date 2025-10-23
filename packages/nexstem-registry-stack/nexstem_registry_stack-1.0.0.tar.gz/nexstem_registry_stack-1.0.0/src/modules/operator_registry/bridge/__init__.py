"""
Bridge module for Operator Registry FFI integration.

This module provides the CFFI-based bridge layer for communicating with
the native operator registry library.
"""

from .operator_registry_bridge import OperatorRegistryBridge

__all__ = [
    "OperatorRegistryBridge",
]
