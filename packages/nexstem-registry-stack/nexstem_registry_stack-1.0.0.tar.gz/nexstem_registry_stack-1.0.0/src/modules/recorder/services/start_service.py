"""
Start Service implementation for Recorder operations.

This module provides the service layer for starting recordings,
handling business logic and data transformation.
"""

from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.start_bridge import StartBridge
from ..dto.responses import RecordingStartResponse, RecordingStartData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class StartService:
    """Service for starting recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Start Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = StartBridge(bridge_lib_path)
    
    async def start_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> RecordingStartResponse:
        """
        Start a recording.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to start
            
        Returns:
            Recording start response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.start_recording(
                base_path=base_path,
                recording_id=recording_id
            )
            
            # Parse response
            if result.get("status") == "success":
                start_data = result.get("data", {})
                
                # Convert timestamp from milliseconds to ISO string
                if isinstance(start_data.get("startTime"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(start_data["startTime"] / 1000)
                    start_data["start_time"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    start_data.pop("startTime", None)
                
                # Remove extra fields to match Node.js response
                start_data.pop("status", None)
                start_data.pop("message", None)
                
                data = RecordingStartData(**start_data)
                
                return RecordingStartResponse(
                    status=ResponseStatus.SUCCESS,
                    message="Recording started",
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingStartResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to start recording"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording start operation failed: {e}")
