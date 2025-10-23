"""
Response DTOs for Pipeline Registry operations.

This module defines the response classes used for various Pipeline Registry operations.
"""

from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field
from shared.dto.common import CliResponse
from .pipeline import Pipeline
from .pipeline_info import PipelineInfo


class PipelineListData(BaseModel):
    """Data for pipeline list response matching Node.js format exactly."""
    
    pipelines: Optional[List[Union[Pipeline, str]]] = Field(
        default=None,
        description="List of pipelines (objects for local, strings for remote)"
    )


class PipelineInstallData(BaseModel):
    """Data for pipeline install response."""
    
    id: str = Field(
        description="Pipeline ID"
    )
    version: str = Field(
        description="Pipeline version"
    )
    action: str = Field(
        description="Action performed (installed, reinstalled, already_installed)"
    )


class PipelineRemoveData(BaseModel):
    """Data for pipeline remove response."""
    
    id: str = Field(
        description="Pipeline ID"
    )
    version: str = Field(
        description="Pipeline version"
    )


class PipelinePushData(BaseModel):
    """Data for pipeline push response."""
    
    id: str = Field(
        description="Pipeline ID"
    )
    version: str = Field(
        description="Pipeline version"
    )
    action: str = Field(
        description="Action performed (pushed, already_exists)"
    )
    registry_url: Optional[str] = Field(
        default=None,
        alias="registryUrl",
        description="Registry URL"
    )


class PipelinePullData(BaseModel):
    """Data for pipeline pull response."""
    
    id: str = Field(
        description="Pipeline ID"
    )
    version: str = Field(
        description="Pipeline version"
    )
    action: str = Field(
        description="Action performed (pulled, already_exists, not_found)"
    )


class PipelineStatusData(BaseModel):
    """Data for pipeline status response."""
    
    id: str = Field(
        description="Pipeline ID"
    )
    version: str = Field(
        description="Pipeline version"
    )
    status: str = Field(
        description="Pipeline status (installed, not_installed, error)"
    )
    install_path: Optional[str] = Field(
        default=None,
        alias="installPath",
        description="Installation path"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is error"
    )


class PipelineListResponse(BaseModel):
    """Pipeline list response matching Node.js format exactly."""
    
    data: Optional[PipelineListData] = Field(None, description="Response data")
    error: Optional[Any] = Field(None, description="Error details if any")
    message: str = Field(..., description="Human-readable message")
    status: str = Field(..., description="Response status")


class PipelineInfoResponse(BaseModel):
    """Pipeline info response matching Node.js format exactly."""
    
    data: Optional[PipelineInfo] = Field(None, description="Response data")
    error: Optional[Any] = Field(None, description="Error details if any")
    message: str = Field(..., description="Human-readable message")
    status: str = Field(..., description="Response status")


class PipelinePullResponse(BaseModel):
    """Pipeline pull response matching Node.js format exactly."""
    
    data: Optional[PipelinePullData] = Field(None, description="Response data")
    error: Optional[Any] = Field(None, description="Error details if any")
    message: str = Field(..., description="Human-readable message")
    status: str = Field(..., description="Response status")


class PipelineRemoveResponse(BaseModel):
    """Pipeline remove response matching Node.js format exactly."""
    
    data: Optional[PipelineRemoveData] = Field(None, description="Response data")
    error: Optional[Any] = Field(None, description="Error details if any")
    message: str = Field(..., description="Human-readable message")
    status: str = Field(..., description="Response status")


# Response types
PipelineInstallResponse = CliResponse[PipelineInstallData]
PipelinePushResponse = CliResponse[PipelinePushData]
PipelineStatusResponse = CliResponse[PipelineStatusData]
