"""
Info Service implementation for Recorder operations.

This module provides the service layer for getting recording information,
handling business logic and data transformation.
"""

import json
from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.info_bridge import InfoBridge
from ..dto.responses import RecordingInfoResponse, RecordingInfoData
from ..dto.recording import RecordingMetadata
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class InfoService:
    """Service for getting recording information."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Info Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = InfoBridge(bridge_lib_path)
    
    async def get_recording_info(
        self,
        base_path: str,
        recording_id: str
    ) -> RecordingInfoResponse:
        """
        Get recording information.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to get info for
            
        Returns:
            Recording info response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.get_recording_info(
                base_path=base_path,
                recording_id=recording_id
            )
            
            # Parse response
            if result.get("status") == "success":
                # The bridge returns recording data directly, but RecordingInfoData expects it wrapped in a 'recording' field
                recording_data = result.get("data", {})
                
                # Parse JSON string fields to objects to match Node.js behavior
                if isinstance(recording_data.get("subject"), str):
                    try:
                        recording_data["subject"] = json.loads(recording_data["subject"])
                    except json.JSONDecodeError:
                        recording_data["subject"] = {}
                
                if isinstance(recording_data.get("channels"), str):
                    try:
                        recording_data["channels"] = json.loads(recording_data["channels"])
                    except json.JSONDecodeError:
                        recording_data["channels"] = []
                
                if isinstance(recording_data.get("filters"), str):
                    try:
                        recording_data["filters"] = json.loads(recording_data["filters"])
                    except json.JSONDecodeError:
                        recording_data["filters"] = []
                
                if isinstance(recording_data.get("markers"), str):
                    try:
                        recording_data["markers"] = json.loads(recording_data["markers"])
                    except json.JSONDecodeError:
                        recording_data["markers"] = []
                
                if isinstance(recording_data.get("meta"), str):
                    try:
                        recording_data["meta"] = json.loads(recording_data["meta"])
                    except json.JSONDecodeError:
                        recording_data["meta"] = {}
                
                # Convert timestamps to ISO strings
                if isinstance(recording_data.get("createdAt"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(recording_data["createdAt"] / 1000)
                    recording_data["createdAt"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                if isinstance(recording_data.get("updatedAt"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(recording_data["updatedAt"] / 1000)
                    recording_data["updatedAt"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                if isinstance(recording_data.get("startedAt"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(recording_data["startedAt"] / 1000)
                    recording_data["startedAt"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                if isinstance(recording_data.get("stoppedAt"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(recording_data["stoppedAt"] / 1000)
                    recording_data["stoppedAt"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Create recording metadata
                recording = RecordingMetadata(**recording_data)
                
                # Wrap in info data
                data = RecordingInfoData(recording=recording)
                
                return RecordingInfoResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Recording info retrieved successfully"),
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingInfoResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to get recording info"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording info operation failed: {e}")
