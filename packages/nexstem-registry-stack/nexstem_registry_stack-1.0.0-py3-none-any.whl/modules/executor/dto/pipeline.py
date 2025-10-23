"""
Pipeline data models for Executor operations.

This module defines the pipeline-related data models used in Executor operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DESTROYED = "destroyed"
    ERROR = "error"
    UNKNOWN = "unknown"


class PipelineRun(BaseModel):
    """Pipeline run information structure."""
    
    run_id: str = Field(
        alias="runId",
        description="Unique run identifier"
    )
    pipeline_id: str = Field(
        alias="pipelineId",
        description="Pipeline ID (name:version)"
    )
    pipeline_name: str = Field(
        alias="pipelineName",
        description="Pipeline name"
    )
    pipeline_version: str = Field(
        alias="pipelineVersion",
        description="Pipeline version"
    )
    status: PipelineStatus = Field(
        description="Current execution status"
    )
    device_id: Optional[str] = Field(
        default=None,
        alias="deviceId",
        description="Associated device ID"
    )
    process_id: Optional[int] = Field(
        default=None,
        alias="processId",
        description="Process ID if running"
    )
    working_directory: Optional[str] = Field(
        default=None,
        alias="workingDirectory",
        description="Working directory"
    )
    command_line_args: Optional[List[str]] = Field(
        default=None,
        alias="commandLineArgs",
        description="Command line arguments"
    )
    created_at: str = Field(
        alias="createdAt",
        description="Creation timestamp"
    )
    started_at: Optional[str] = Field(
        default=None,
        alias="startedAt",
        description="Start timestamp"
    )
    stopped_at: Optional[str] = Field(
        default=None,
        alias="stoppedAt",
        description="Stop timestamp"
    )
    destroyed_at: Optional[str] = Field(
        default=None,
        alias="destroyedAt",
        description="Destroy timestamp"
    )
    log_file_location: Optional[str] = Field(
        default=None,
        alias="logFileLocation",
        description="Log file location"
    )
    pipeline_config: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="pipelineConfig",
        description="Pipeline configuration"
    )
    
    class Config:
        validate_by_name = True
        use_enum_values = True
