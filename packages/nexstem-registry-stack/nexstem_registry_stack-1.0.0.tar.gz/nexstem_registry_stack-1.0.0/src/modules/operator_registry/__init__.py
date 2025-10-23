"""
Operator Registry module for SW Registry Stack Python SDK.

This module provides the OperatorRegistry service following the same structure
as the Node.js SDK.
"""

from .operator_registry import OperatorRegistry
from .config import OperatorRegistryConfiguration
from .dto import (
    OperatorListOptions,
    OperatorInstallOptions,
    OperatorUninstallOptions,
    OperatorInfoOptions,
    OperatorStatusOptions,
    OperatorPushOptions,
    OperatorRepairOptions,
    OperatorListResponse,
    OperatorInstallResponse,
    OperatorUninstallResponse,
    OperatorInfoResponse,
    OperatorStatusResponse,
    OperatorPushResponse,
    OperatorRepairResponse,
    Operator,
    OperatorListData,
    OperatorInstallData,
    OperatorUninstallData,
    OperatorStatusData,
    OperatorPushData,
    OperatorRepairData,
)

__all__ = [
    "OperatorRegistry",
    "OperatorRegistryConfiguration",
    # Options
    "OperatorListOptions",
    "OperatorInstallOptions",
    "OperatorUninstallOptions",
    "OperatorInfoOptions",
    "OperatorStatusOptions",
    "OperatorPushOptions",
    "OperatorRepairOptions",
    # Responses
    "OperatorListResponse",
    "OperatorInstallResponse",
    "OperatorUninstallResponse",
    "OperatorInfoResponse",
    "OperatorStatusResponse",
    "OperatorPushResponse",
    "OperatorRepairResponse",
    # Data models
    "Operator",
    "OperatorListData",
    "OperatorInstallData",
    "OperatorUninstallData",
    "OperatorStatusData",
    "OperatorPushData",
    "OperatorRepairData",
]
