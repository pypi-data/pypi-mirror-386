"""
Bridge module for Pipeline Registry operations.

This module provides the bridge layer for Pipeline Registry operations,
handling the CFFI integration with the native C++ library.
"""

from .pipeline_registry_bridge import PipelineRegistryBridge

__all__ = [
    "PipelineRegistryBridge",
]
