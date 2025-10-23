"""
Data Transfer Objects (DTOs) for Recorder operations.

This module contains all the DTOs used for Recorder operations,
including options, responses, and data models.
"""

from .options import (
    RecorderListOptions,
    RecorderCreateOptions,
    RecorderUpdateOptions,
    RecorderDownloadOptions,
)
from .recording import RecordingStatus, RecordingMarker, RecordingMetadata
from .responses import (
    RecordingListData,
    RecordingCreateData,
    RecordingUpdateData,
    RecordingInfoData,
    RecordingDownloadData,
    RecordingDeleteData,
    RecordingStartData,
    RecordingStopData,
    RecordingTotalDurationData,
    RecordingListResponse,
    RecordingCreateResponse,
    RecordingUpdateResponse,
    RecordingInfoResponse,
    RecordingDownloadResponse,
    RecordingDeleteResponse,
    RecordingStartResponse,
    RecordingStopResponse,
    RecordingTotalDurationResponse,
)
from .config import RecorderConfig

__all__ = [
    # Options
    "RecorderListOptions",
    "RecorderCreateOptions",
    "RecorderUpdateOptions",
    "RecorderDownloadOptions",
    # Data models
    "RecordingStatus",
    "RecordingMarker",
    "RecordingMetadata",
    "RecordingListData",
    "RecordingCreateData",
    "RecordingUpdateData",
    "RecordingInfoData",
    "RecordingDownloadData",
    "RecordingDeleteData",
    "RecordingStartData",
    "RecordingStopData",
    "RecordingTotalDurationData",
    # Responses
    "RecordingListResponse",
    "RecordingCreateResponse",
    "RecordingUpdateResponse",
    "RecordingInfoResponse",
    "RecordingDownloadResponse",
    "RecordingDeleteResponse",
    "RecordingStartResponse",
    "RecordingStopResponse",
    "RecordingTotalDurationResponse",
    # Config
    "RecorderConfig",
]
