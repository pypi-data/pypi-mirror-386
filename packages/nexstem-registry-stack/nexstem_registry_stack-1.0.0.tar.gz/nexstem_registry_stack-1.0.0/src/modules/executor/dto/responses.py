"""
Executor response DTOs.

This module defines the response classes for Executor operations,
including data structures and response wrappers.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from shared.dto.common import CliResponse, ResponseStatus


class PipelineRun(BaseModel):
    """Pipeline run information structure."""
    
    created_at: int = Field(..., description="Creation timestamp (Unix timestamp)")
    device_id: str = Field(..., description="Associated device ID")
    pipeline_id: str = Field(..., description="Pipeline ID (name:version)")
    pipeline_name: str = Field(..., description="Pipeline name")
    pipeline_version: str = Field(..., description="Pipeline version")
    process_id: int = Field(..., description="Process ID if running")
    run_id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="Current execution status")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineCreateData(BaseModel):
    """Pipeline creation response data."""
    
    run_id: str = Field(..., description="Unique run identifier")
    pipeline_id: str = Field(..., description="Pipeline ID (name:version)")
    device_id: Optional[str] = Field(default=None, description="Associated device ID")
    process_id: Optional[int] = Field(default=None, description="Process ID if running")
    state: str = Field(..., description="Current pipeline state")
    background: bool = Field(..., description="Whether running in background")
    created_at: int = Field(..., description="Creation timestamp (Unix timestamp)")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineStateTransitionData(BaseModel):
    """Pipeline state transition response data."""
    
    run_id: str = Field(..., description="Unique run identifier")
    pipeline_id: str = Field(..., description="Pipeline ID (name:version)")
    current_state: str = Field(..., description="State before transition")
    new_state: str = Field(..., description="State after transition")
    timestamp: Optional[str] = Field(default=None, description="Transition timestamp")
    zmq_address: Optional[str] = Field(default=None, description="ZMQ socket address for signals")
    action: Optional[str] = Field(default=None, description="Action performed")
    valid_states: Optional[List[str]] = Field(default=None, description="Valid states for the operation")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineListData(BaseModel):
    """Pipeline list response data."""
    
    pipelines: List[PipelineRun] = Field(..., description="List of pipeline runs")
    count: int = Field(..., description="Total number of pipelines")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineHistoryData(BaseModel):
    """Pipeline history response data."""
    
    count: int = Field(..., description="Total number of history entries")
    runs: List[PipelineRun] = Field(..., description="Array of historical pipeline runs")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineInfoData(BaseModel):
    """Pipeline info response data."""
    
    pipeline: PipelineRun = Field(..., description="Pipeline run information")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineRunHistoryData(BaseModel):
    """Pipeline run history response data."""
    
    run_id: str = Field(..., description="Unique run identifier")
    history: List[Dict[str, Any]] = Field(..., description="Pipeline execution history")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineValidationData(BaseModel):
    """Pipeline validation response data."""
    
    valid: bool = Field(..., description="Whether pipeline is valid")
    errors: Optional[List[str]] = Field(default=None, description="Validation errors")
    warnings: Optional[List[str]] = Field(default=None, description="Validation warnings")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class PipelineSignalData(BaseModel):
    """Pipeline signal response data."""
    
    run_id: str = Field(..., description="Unique run identifier")
    signal: str = Field(..., description="Signal name")
    node_ids: Optional[List[str]] = Field(default=None, description="Target node IDs")
    signal_args: Optional[Dict[str, Any]] = Field(default=None, description="Signal arguments")
    zmq_status: str = Field(..., description="ZMQ status")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class ExecutorVersionData(BaseModel):
    """Executor version response data."""
    
    name: str = Field(..., description="Executor name")
    version: str = Field(..., description="Executor version")
    
    class Config:
        validate_by_name = True
        extra = "forbid"


# Response type aliases
PipelineCreateResponse = CliResponse[PipelineCreateData]
PipelineStateTransitionResponse = CliResponse[PipelineStateTransitionData]
PipelineListResponse = CliResponse[PipelineListData]
PipelineInfoResponse = CliResponse[PipelineRun]
PipelineHistoryResponse = CliResponse[PipelineHistoryData]
PipelineValidationResponse = CliResponse[PipelineValidationData]
PipelineSignalResponse = CliResponse[PipelineSignalData]
ExecutorVersionResponse = CliResponse[ExecutorVersionData]