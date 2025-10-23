"""
Response DTOs for Operator Registry operations.

This module provides response data models for all Operator Registry operations,
following the same structure as the Node.js SDK.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import CliResponse
from .operator import Operator
from .operator_info import OperatorInfo


class OperatorListData(BaseModel):
    """Data structure for operator list responses."""
    
    count: int = Field(..., ge=0, description="Total number of operators")
    operators: Optional[List[Union[Operator, str]]] = Field(None, description="List of operators (objects for local, strings for remote)")
    versions: Optional[List[str]] = Field(None, description="List of versions (for remote versions queries)")


class OperatorInstallData(BaseModel):
    """Data structure for operator install responses."""
    
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")
    platform: Optional[str] = Field(None, description="Target platform")
    action: str = Field(..., description="Action performed (installed, reinstalled, already_installed)")


class OperatorUninstallData(BaseModel):
    """Data structure for operator uninstall responses."""
    
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")


class OperatorStatusData(BaseModel):
    """Data structure for operator status responses."""
    
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")
    status: str = Field(..., description="Installation status")
    install_path: Optional[str] = Field(None, description="Installation path")
    error: Optional[str] = Field(None, description="Error message if status is error")


class OperatorPushData(BaseModel):
    """Data structure for operator push responses."""
    
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")
    action: str = Field(..., description="Action performed (pushed, already_exists)")
    registry_url: Optional[str] = Field(None, description="Registry URL")


class OperatorRepairData(BaseModel):
    """Data structure for operator repair responses."""
    
    repaired: int = Field(..., ge=0, description="Number of operators repaired")
    removed: int = Field(..., ge=0, description="Number of operators removed")
    status: str = Field(..., description="Repair status (completed, partial, failed)")


# Response type aliases
OperatorListResponse = CliResponse[OperatorListData]
OperatorInstallResponse = CliResponse[OperatorInstallData]
OperatorUninstallResponse = CliResponse[OperatorUninstallData]
OperatorInfoResponse = CliResponse[OperatorInfo]
OperatorStatusResponse = CliResponse[OperatorStatusData]
OperatorPushResponse = CliResponse[OperatorPushData]
OperatorRepairResponse = CliResponse[OperatorRepairData]
