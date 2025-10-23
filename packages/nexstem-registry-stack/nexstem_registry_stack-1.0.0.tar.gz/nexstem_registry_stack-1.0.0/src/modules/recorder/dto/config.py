"""
Configuration DTOs for Recorder operations.

This module defines the configuration classes used for Recorder operations.
"""

from typing import Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import BaseConfig


class RecorderConfig(BaseConfig):
    """Configuration for Recorder operations."""
    
    base_path: str = Field(
        default="/opt/recordings",
        description="Base path for recording storage"
    )
    bridge_lib_path: str = Field(
        description="Path to the recorder bridge library"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    timeout: int = Field(
        default=30000,
        description="Timeout for operations in milliseconds"
    )
    max_concurrent_recordings: int = Field(
        default=5,
        alias="maxConcurrentRecordings",
        description="Maximum number of concurrent recordings"
    )
    log_level: str = Field(
        default="info",
        alias="logLevel",
        description="Log level (debug, info, warn, error)"
    )
    log_file: Optional[str] = Field(
        default=None,
        alias="logFile",
        description="Log file path"
    )
    default_device_id: Optional[str] = Field(
        default=None,
        alias="defaultDeviceId",
        description="Default device ID"
    )
    auto_cleanup: bool = Field(
        default=True,
        alias="autoCleanup",
        description="Automatically cleanup old recordings"
    )
    cleanup_interval: int = Field(
        default=86400,
        alias="cleanupInterval",
        description="Cleanup interval in seconds"
    )
    max_recording_duration: int = Field(
        default=3600,
        alias="maxRecordingDuration",
        description="Maximum recording duration in seconds"
    )
    compression_enabled: bool = Field(
        default=True,
        alias="compressionEnabled",
        description="Enable compression for recordings"
    )
