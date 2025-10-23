"""
Shared components for the SW Registry Stack Python SDK.

This package contains shared utilities, types, and components used
across all service modules.
"""

from .dto import (
    BaseConfig,
    CliResponse,
    ErrorDetails,
    PaginationOptions,
    OperationOptions,
    Platform,
    VersionInfo,
)

__all__ = [
    "BaseConfig",
    "CliResponse",
    "ErrorDetails",
    "PaginationOptions",
    "OperationOptions",
    "Platform",
    "VersionInfo",
]
