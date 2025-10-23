"""
Recording data models for Recorder operations.

This module defines the recording-related data models used in Recorder operations.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import IntEnum
from datetime import datetime


class RecordingStatus(IntEnum):
    """Recording status enumeration."""
    
    IDLE = 0
    RECORDING = 1
    PAUSED = 2
    STOPPED = 3
    ERROR = 4


class RecordingMarker(BaseModel):
    """Recording marker structure for annotations."""
    
    id: str = Field(
        description="Marker ID"
    )
    start_time_sec: float = Field(
        alias="startTimeSec",
        description="Start time in seconds"
    )
    end_time_sec: float = Field(
        alias="endTimeSec",
        description="End time in seconds"
    )
    code: str = Field(
        description="Marker code"
    )
    label: str = Field(
        description="Marker label"
    )
    channel: Optional[str] = Field(
        default=None,
        description="Channel name"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source name"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Marker tags"
    )
    extra: Optional[str] = Field(
        default=None,
        description="Extra information"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Marker notes"
    )
    
    class Config:
        validate_by_name = True


class RecordingMetadata(BaseModel):
    """Recording metadata structure."""
    
    id: str = Field(
        description="Recording ID"
    )
    name: str = Field(
        description="Recording name"
    )
    file_path: str = Field(
        alias="filePath",
        description="File path"
    )
    device_id: str = Field(
        alias="deviceId",
        description="Device ID"
    )
    subject: Union[Dict[str, Any], str] = Field(
        description="Subject information"
    )
    graph: str = Field(
        description="Graph configuration"
    )
    channels: Union[List[Dict[str, Any]], str] = Field(
        description="Channels configuration"
    )
    filters: Union[List[Dict[str, Any]], str] = Field(
        description="Filters configuration"
    )
    markers: Union[List[Dict[str, Any]], str] = Field(
        description="Markers configuration"
    )
    meta: Union[Dict[str, Any], str] = Field(
        default={},
        description="Recording metadata"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Recording notes"
    )
    status: RecordingStatus = Field(
        default=RecordingStatus.STOPPED,
        description="Recording status"
    )
    created_at: str = Field(
        alias="createdAt",
        description="Creation timestamp"
    )
    updated_at: str = Field(
        alias="updatedAt",
        description="Last update timestamp"
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
    duration_sec: Optional[float] = Field(
        default=None,
        alias="durationSec",
        description="Duration in seconds"
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        alias="fileSizeBytes",
        description="File size in bytes"
    )
    
    @validator('created_at', 'updated_at', pre=True)
    def convert_timestamp(cls, v):
        """Convert integer timestamp to string if needed."""
        if isinstance(v, int):
            # Convert Unix timestamp (milliseconds) to ISO string
            dt = datetime.fromtimestamp(v / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return v
    
    @validator('started_at', 'stopped_at', pre=True)
    def convert_optional_timestamp(cls, v):
        """Convert optional integer timestamp to string if needed."""
        if v is not None and isinstance(v, int):
            # Convert Unix timestamp (milliseconds) to ISO string
            dt = datetime.fromtimestamp(v / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return v
    
    class Config:
        validate_by_name = True
        use_enum_values = True
