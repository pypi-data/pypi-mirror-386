"""
Executor options DTOs.

This module defines the options classes for Executor operations,
including validation and default values.
"""

from typing import Optional, Dict, Any, Union, Callable
from pydantic import BaseModel, Field, validator


class OperationOptions(BaseModel):
    """Base options for executor operations."""
    
    pretty: bool = Field(
        default=False,
        description="Enable pretty printing"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class ExecutorCreateOptions(OperationOptions):
    """Options for creating a pipeline."""
    
    device_id: Optional[str] = Field(
        default=None,
        description="Device ID to associate with the pipeline"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration overrides"
    )
    background: bool = Field(
        default=True,
        description="Run executor in background (detached)"
    )
    json_data: bool = Field(
        default=False,
        description="Flag to indicate JSON data input"
    )
    enable_logging: bool = Field(
        default=False,
        description="Enable unified logging"
    )
    on_unified_log: Optional[Callable] = Field(
        default=None,
        description="Unified logging callback function"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('device_id')
    def validate_device_id(cls, v):
        """Validate device ID format."""
        if v is not None and not v.strip():
            raise ValueError("Device ID cannot be empty")
        return v
    
    def model_dump_for_bridge(self) -> Dict[str, Any]:
        """Get options data suitable for bridge operations."""
        return {
            "deviceId": self.device_id,
            "config": self.config,
            "background": self.background,
            "jsonData": self.json_data,
            "pretty": self.pretty
        }


class ExecutorStartOptions(OperationOptions):
    """Options for starting a pipeline."""
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class ExecutorStopOptions(OperationOptions):
    """Options for stopping a pipeline."""
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class ExecutorDestroyOptions(OperationOptions):
    """Options for destroying a pipeline."""
    
    class Config:
        validate_by_name = True
        extra = "forbid"


class ExecutorListOptions(OperationOptions):
    """Options for listing pipelines."""
    
    status: Optional[str] = Field(
        default=None,
        description="Filter by pipeline status"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term for pipeline name or device ID"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of pipelines to return"
    )
    offset: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of pipelines to skip"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status format."""
        if v is not None and not v.strip():
            raise ValueError("Status cannot be empty")
        return v
    
    @validator('search')
    def validate_search(cls, v):
        """Validate search term format."""
        if v is not None and not v.strip():
            raise ValueError("Search term cannot be empty")
        return v


class ExecutorInfoOptions(OperationOptions):
    """Options for getting pipeline info."""
    
    json_file: Optional[str] = Field(
        default=None,
        description="Path to JSON file"
    )
    json_data: Optional[str] = Field(
        default=None,
        description="Inline JSON data"
    )
    run_id: Optional[str] = Field(
        default=None,
        description="Pipeline run ID"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('json_file')
    def validate_json_file(cls, v):
        """Validate JSON file path."""
        if v is not None and not v.strip():
            raise ValueError("JSON file path cannot be empty")
        return v
    
    @validator('json_data')
    def validate_json_data(cls, v):
        """Validate JSON data."""
        if v is not None and not v.strip():
            raise ValueError("JSON data cannot be empty")
        return v
    
    @validator('run_id')
    def validate_run_id(cls, v):
        """Validate run ID format."""
        if v is not None and not v.strip():
            raise ValueError("Run ID cannot be empty")
        return v


class ExecutorHistoryOptions(OperationOptions):
    """Options for getting pipeline history."""
    
    pipeline_id: Optional[str] = Field(
        default=None,
        description="Filter by pipeline ID (name:version)"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of entries to return"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('pipeline_id')
    def validate_pipeline_id(cls, v):
        """Validate pipeline ID format."""
        if v is not None and not v.strip():
            raise ValueError("Pipeline ID cannot be empty")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status format."""
        if v is not None and not v.strip():
            raise ValueError("Status cannot be empty")
        return v


class ExecutorValidateOptions(OperationOptions):
    """Options for validating a pipeline."""
    
    pipeline_spec: str = Field(
        ...,
        description="Pipeline specification to validate"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('pipeline_spec')
    def validate_pipeline_spec(cls, v):
        """Validate pipeline specification format."""
        if not v or not v.strip():
            raise ValueError("Pipeline specification is required")
        return v.strip()


class ExecutorSignalOptions(OperationOptions):
    """Options for sending signals to a pipeline."""
    
    run_id: str = Field(
        ...,
        description="Run ID of the pipeline"
    )
    signal: str = Field(
        ...,
        description="Signal name to send"
    )
    node_ids: Optional[list[str]] = Field(
        default=None,
        description="Target node IDs"
    )
    signal_args: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Signal arguments"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('run_id')
    def validate_run_id(cls, v):
        """Validate run ID format."""
        if not v or not v.strip():
            raise ValueError("Run ID is required")
        return v.strip()
    
    @validator('signal')
    def validate_signal(cls, v):
        """Validate signal name."""
        if not v or not v.strip():
            raise ValueError("Signal name is required")
        return v.strip()


class ExecutorVersionOptions(OperationOptions):
    """Options for getting executor version."""
    
    class Config:
        validate_by_name = True
        extra = "forbid"