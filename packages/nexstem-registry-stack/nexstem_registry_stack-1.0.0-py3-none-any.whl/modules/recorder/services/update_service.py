"""
Update Service implementation for Recorder operations.

This module provides the service layer for updating recordings,
handling business logic and data transformation.
"""

import json
from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.update_bridge import UpdateBridge
from ..dto.responses import RecordingUpdateResponse
from ..dto.recording import RecordingMetadata
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class UpdateService:
    """Service for updating recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Update Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = UpdateBridge(bridge_lib_path)
    
    async def update_recording(
        self,
        base_path: str,
        recording_id: str,
        options
    ) -> RecordingUpdateResponse:
        """
        Update a recording.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to update
            options: Update options
            
        Returns:
            Recording update response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Convert options to JSON data
            json_data = {
                "name": options.name,
                "subject": json.dumps(options.subject or {}),
                "graph": options.graph or "",
                "channels": json.dumps(options.channels or []),
                "filters": json.dumps([options.filters] if options.filters else []),
                "markers": json.dumps(options.markers or []),
                "notes": options.notes or ""
            }
            
            # Call bridge
            result = await self.bridge.update_recording(
                base_path=base_path,
                recording_id=recording_id,
                json_data=json.dumps(json_data)
            )
            
            # Parse response
            if result.get("status") == "success":
                # The bridge returns recording data directly
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
                data = RecordingMetadata(**recording_data)
                
                return RecordingUpdateResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Recording updated successfully"),
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingUpdateResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to update recording"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording update operation failed: {e}")
