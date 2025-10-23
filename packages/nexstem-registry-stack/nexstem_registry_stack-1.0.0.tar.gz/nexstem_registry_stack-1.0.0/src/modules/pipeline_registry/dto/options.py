"""
Options DTOs for Pipeline Registry operations.

This module defines the options classes used for various Pipeline Registry operations.
"""

from typing import Optional
from pydantic import BaseModel, Field
from shared.dto.common import PaginationOptions, OperationOptions


class PipelineListOptions(PaginationOptions, OperationOptions):
    """Options for listing pipelines."""
    
    remote: Optional[bool] = Field(
        default=False,
        description="Whether to list remote pipelines"
    )
    pipeline: Optional[str] = Field(
        default=None,
        description="Filter by pipeline ID"
    )
    versions: Optional[bool] = Field(
        default=False,
        description="Whether to list versions"
    )


class PipelineInfoOptions(OperationOptions):
    """Options for getting pipeline information."""
    
    remote: Optional[bool] = Field(
        default=False,
        description="Whether to get remote pipeline info"
    )
    extend: Optional[bool] = Field(
        default=False,
        description="Whether to get extended information"
    )


class PipelinePushOptions(OperationOptions):
    """Options for pushing pipelines."""
    
    local: Optional[bool] = Field(
        default=False,
        description="Whether to only register locally"
    )
    pipeline_json: Optional[str] = Field(
        default=None,
        alias="pipelineJson",
        description="Inline pipeline JSON"
    )


class PipelinePullOptions(OperationOptions):
    """Options for pulling pipelines."""
    
    force: Optional[bool] = Field(
        default=False,
        description="Force reinstall if already exists"
    )


class PipelineRemoveOptions(OperationOptions):
    """Options for removing pipelines."""
    
    force: Optional[bool] = Field(
        default=False,
        description="Force removal"
    )


class PipelineStatusOptions(OperationOptions):
    """Options for checking pipeline status."""
    pass
