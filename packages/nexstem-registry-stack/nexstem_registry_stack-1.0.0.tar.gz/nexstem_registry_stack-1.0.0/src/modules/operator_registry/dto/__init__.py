"""
DTO (Data Transfer Objects) for Operator Registry operations.

This module provides data models for options, responses, and entities
used in Operator Registry operations.
"""

from .options import (
    OperatorListOptions,
    OperatorInstallOptions,
    OperatorUninstallOptions,
    OperatorInfoOptions,
    OperatorStatusOptions,
    OperatorPushOptions,
    OperatorRepairOptions,
)

from .responses import (
    OperatorListResponse,
    OperatorInstallResponse,
    OperatorUninstallResponse,
    OperatorInfoResponse,
    OperatorStatusResponse,
    OperatorPushResponse,
    OperatorRepairResponse,
    OperatorListData,
    OperatorInstallData,
    OperatorUninstallData,
    OperatorStatusData,
    OperatorPushData,
    OperatorRepairData,
)

from .operator import Operator

__all__ = [
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
    "OperatorListData",
    "OperatorInstallData",
    "OperatorUninstallData",
    "OperatorStatusData",
    "OperatorPushData",
    "OperatorRepairData",
    # Entities
    "Operator",
]
