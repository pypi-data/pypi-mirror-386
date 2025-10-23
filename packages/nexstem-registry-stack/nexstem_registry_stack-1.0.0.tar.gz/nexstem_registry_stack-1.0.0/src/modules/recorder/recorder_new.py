"""
Recorder service implementation with modular architecture.

This module provides the main Recorder class for managing recordings
in the SW Registry Stack, using individual service classes for each operation.
"""

import asyncio
import json
from typing import Optional, Union, Dict, Any, List
from .dto import (
    RecorderConfig,
    RecorderListOptions,
    RecorderCreateOptions,
    RecorderUpdateOptions,
    RecorderDownloadOptions,
    RecordingListResponse,
    RecordingCreateResponse,
    RecordingUpdateResponse,
    RecordingInfoResponse,
    RecordingDownloadResponse,
    RecordingDeleteResponse,
    RecordingStartResponse,
    RecordingStopResponse,
    RecordingTotalDurationResponse,
    RecordingListData,
    RecordingCreateData,
    RecordingInfoData,
    RecordingDownloadData,
    RecordingDeleteData,
    RecordingStartData,
    RecordingStopData,
    RecordingTotalDurationData,
    RecordingMetadata,
)
from .services import (
    ListService,
    CreateService,
    InfoService,
    UpdateService,
    StartService,
    StopService,
    DeleteService,
    DownloadService,
    DurationService
)
from shared.dto.common import CliResponse, ResponseStatus
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from exceptions import (
    SdkError,
    ValidationError,
    FfiBridgeError,
    ConfigurationError,
)


class Recorder:
    """
    Main Recorder class for managing recordings.
    
    This class provides a high-level interface for all recorder operations,
    delegating to individual service classes for modularity and maintainability.
    """
    
    def __init__(self, config: RecorderConfig):
        """
        Initialize the Recorder.
        
        Args:
            config: Recorder configuration
        """
        self.config = config
        self._is_initialized = False
        
        # Initialize individual services
        self._list_service = ListService(config.bridge_lib_path)
        self._create_service = CreateService(config.bridge_lib_path)
        self._info_service = InfoService(config.bridge_lib_path)
        self._update_service = UpdateService(config.bridge_lib_path)
        self._start_service = StartService(config.bridge_lib_path)
        self._stop_service = StopService(config.bridge_lib_path)
        self._delete_service = DeleteService(config.bridge_lib_path)
        self._download_service = DownloadService(config.bridge_lib_path)
        self._duration_service = DurationService(config.bridge_lib_path)
    
    async def initialize(self) -> None:
        """Initialize the recorder service."""
        if not self._is_initialized:
            # Initialize all services
            await asyncio.gather(
                self._list_service.initialize(),
                self._create_service.initialize(),
                self._info_service.initialize(),
                self._update_service.initialize(),
                self._start_service.initialize(),
                self._stop_service.initialize(),
                self._delete_service.initialize(),
                self._download_service.initialize(),
                self._duration_service.initialize()
            )
            self._is_initialized = True
    
    async def list(
        self,
        options: Optional[RecorderListOptions] = None
    ) -> RecordingListResponse:
        """
        List recordings.
        
        Args:
            options: List options
            
        Returns:
            Recording list response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._list_service.list_recordings(
            base_path=self.config.base_path,
            options=options
        )
    
    async def create(
        self,
        options: RecorderCreateOptions
    ) -> RecordingCreateResponse:
        """
        Create a recording.
        
        Args:
            options: Create options
            
        Returns:
            Recording create response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._create_service.create_recording(
            base_path=self.config.base_path,
            options=options
        )
    
    async def info(
        self,
        recording_id: str
    ) -> RecordingInfoResponse:
        """
        Get recording information.
        
        Args:
            recording_id: Recording ID
            
        Returns:
            Recording info response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._info_service.get_recording_info(
            base_path=self.config.base_path,
            recording_id=recording_id
        )
    
    async def update(
        self,
        recording_id: str,
        options: RecorderUpdateOptions
    ) -> RecordingUpdateResponse:
        """
        Update a recording.
        
        Args:
            recording_id: Recording ID
            options: Update options
            
        Returns:
            Recording update response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._update_service.update_recording(
            base_path=self.config.base_path,
            recording_id=recording_id,
            options=options
        )
    
    async def start(
        self,
        recording_id: str
    ) -> RecordingStartResponse:
        """
        Start a recording.
        
        Args:
            recording_id: Recording ID
            
        Returns:
            Recording start response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._start_service.start_recording(
            base_path=self.config.base_path,
            recording_id=recording_id
        )
    
    async def stop(
        self,
        recording_id: str
    ) -> RecordingStopResponse:
        """
        Stop a recording.
        
        Args:
            recording_id: Recording ID
            
        Returns:
            Recording stop response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._stop_service.stop_recording(
            base_path=self.config.base_path,
            recording_id=recording_id
        )
    
    async def delete(
        self,
        recording_id: str
    ) -> RecordingDeleteResponse:
        """
        Delete a recording.
        
        Args:
            recording_id: Recording ID
            
        Returns:
            Recording delete response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._delete_service.delete_recording(
            base_path=self.config.base_path,
            recording_id=recording_id
        )
    
    async def download(
        self,
        recording_id: str,
        options: RecorderDownloadOptions
    ) -> RecordingDownloadResponse:
        """
        Download a recording.
        
        Args:
            recording_id: Recording ID
            options: Download options
            
        Returns:
            Recording download response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._download_service.download_recording(
            base_path=self.config.base_path,
            recording_id=recording_id,
            destination=options.destination
        )
    
    async def total_duration(self) -> RecordingTotalDurationResponse:
        """
        Get total duration of all recordings.
        
        Returns:
            Recording total duration response
        """
        if not self._is_initialized:
            await self.initialize()
        
        return await self._duration_service.get_total_duration(
            base_path=self.config.base_path
        )
