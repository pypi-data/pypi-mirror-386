"""
Options DTOs for Operator Registry operations.

This module provides option classes for all Operator Registry operations,
following the same structure as the Node.js SDK.
"""

from typing import Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import PaginationOptions, OperationOptions


class OperatorListOptions(PaginationOptions, OperationOptions):
    """Options for listing operators."""
    
    remote: Optional[bool] = Field(None, description="List remote operators instead of local")
    operator: Optional[str] = Field(None, description="Filter by operator name")
    versions: Optional[bool] = Field(None, description="List versions for specific operator")


class OperatorInstallOptions(OperationOptions):
    """Options for installing operators."""
    
    platform: Optional[str] = Field(None, description="Target platform (e.g., 'linux/amd64')")
    force: Optional[bool] = Field(None, description="Force reinstall even if already installed")


class OperatorUninstallOptions(OperationOptions):
    """Options for uninstalling operators."""
    pass


class OperatorInfoOptions(OperationOptions):
    """Options for getting operator information."""
    
    remote: Optional[bool] = Field(None, description="Get info from remote registry")


class OperatorStatusOptions(OperationOptions):
    """Options for checking operator status."""
    pass


class OperatorPushOptions(OperationOptions):
    """Options for pushing operators."""
    
    local: Optional[bool] = Field(None, description="Only register locally, skip remote push")


class OperatorRepairOptions(OperationOptions):
    """Options for repairing operator registry."""
    pass
