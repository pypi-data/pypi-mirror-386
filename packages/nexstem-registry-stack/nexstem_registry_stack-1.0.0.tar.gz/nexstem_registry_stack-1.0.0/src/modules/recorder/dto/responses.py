"""
Response DTOs for Recorder operations.

This module defines the response classes used for various Recorder operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import CliResponse
from .recording import RecordingMetadata, RecordingStatus


class RecordingListData(BaseModel):
    """Data for recording list response matching Node.js format exactly."""
    
    count: int = Field(
        default=0,
        description="Number of recordings returned"
    )
    limit: int = Field(
        default=0,
        description="Limit applied to the query"
    )
    offset: int = Field(
        default=0,
        description="Offset applied to the query"
    )
    order: str = Field(
        default="DESC",
        description="Order direction"
    )
    orderBy: str = Field(
        default="createdAt",
        description="Field to order by"
    )
    recordings: List[RecordingMetadata] = Field(
        default_factory=list,
        description="List of recordings"
    )
    totalCount: int = Field(
        default=0,
        description="Total number of recordings"
    )
    
    class Config:
        validate_by_name = True


class RecordingCreateData(BaseModel):
    """Data for recording create response matching Node.js format exactly."""
    
    id: str = Field(
        description="Created recording ID"
    )
    name: str = Field(
        description="Recording name"
    )
    filePath: str = Field(
        description="File path"
    )
    deviceId: str = Field(
        description="Device ID"
    )
    subject: Dict[str, Any] = Field(
        description="Subject information"
    )
    graph: str = Field(
        description="Graph configuration"
    )
    channels: List[Dict[str, Any]] = Field(
        description="List of channels"
    )
    filters: List[Dict[str, Any]] = Field(
        description="List of filters"
    )
    markers: List[Dict[str, Any]] = Field(
        description="List of markers"
    )
    meta: Dict[str, Any] = Field(
        description="Metadata"
    )
    createdAt: str = Field(
        description="Creation timestamp"
    )
    updatedAt: str = Field(
        description="Last update timestamp"
    )


class RecordingUpdateData(BaseModel):
    """Data for recording update response."""
    
    id: str = Field(
        description="Updated recording ID"
    )
    name: str = Field(
        description="Recording name"
    )
    updated_at: str = Field(
        alias="updatedAt",
        description="Last update timestamp"
    )
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Changes made"
    )


class RecordingInfoData(BaseModel):
    """Data for recording info response."""
    
    recording: RecordingMetadata = Field(
        description="Recording metadata"
    )


class RecordingDownloadData(BaseModel):
    """Data for recording download response."""
    
    id: str = Field(
        description="Recording ID"
    )
    destination: str = Field(
        description="Download destination path"
    )
    source_path: str = Field(
        alias="sourcePath",
        description="Source file path"
    )
    file_size_bytes: Optional[int] = Field(
        default=None,
        alias="fileSizeBytes",
        description="Downloaded file size in bytes"
    )
    download_time_sec: Optional[float] = Field(
        default=None,
        alias="downloadTimeSec",
        description="Download time in seconds"
    )


class RecordingDeleteData(BaseModel):
    """Data for recording delete response."""
    
    id: str = Field(
        description="Deleted recording ID"
    )
    deleted_at: str = Field(
        alias="deletedAt",
        description="Deletion timestamp"
    )


class RecordingStartData(BaseModel):
    """Data for recording start response."""
    
    id: str = Field(
        description="Recording ID"
    )
    status: Optional[RecordingStatus] = Field(
        default=None,
        description="New recording status"
    )
    start_time: str = Field(
        description="Start timestamp"
    )
    message: Optional[str] = Field(
        default=None,
        description="Start message"
    )


class RecordingStopData(BaseModel):
    """Data for recording stop response."""
    
    id: str = Field(
        description="Recording ID"
    )
    end_time: str = Field(
        description="Stop timestamp"
    )
    duration: int = Field(
        description="Recording duration in milliseconds"
    )


class RecordingTotalDurationData(BaseModel):
    """Data for recording total duration response."""
    
    total_duration_ms: int = Field(
        alias="totalDurationMs",
        description="Total duration in milliseconds"
    )
    total_duration_sec: int = Field(
        alias="totalDurationSec",
        description="Total duration in seconds"
    )


# Custom response classes to match Node.js format exactly
class RecordingListResponse(BaseModel):
    """Recording list response matching Node.js format exactly."""
    data: Optional[RecordingListData] = Field(default=None, description="Recording list data")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    message: str = Field(description="Response message")
    status: str = Field(description="Response status")

# Response types
# RecordingListResponse = CliResponse[RecordingListData]
RecordingCreateResponse = CliResponse[RecordingCreateData]
RecordingUpdateResponse = CliResponse[RecordingMetadata]
RecordingInfoResponse = CliResponse[RecordingInfoData]
RecordingDownloadResponse = CliResponse[RecordingDownloadData]
RecordingDeleteResponse = CliResponse[RecordingDeleteData]
RecordingStartResponse = CliResponse[RecordingStartData]
RecordingStopResponse = CliResponse[RecordingStopData]
RecordingTotalDurationResponse = CliResponse[RecordingTotalDurationData]
