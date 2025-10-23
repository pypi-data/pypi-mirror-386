"""
Stop Service implementation for Recorder operations.

This module provides the service layer for stopping recordings,
handling business logic and data transformation.
"""

from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.stop_bridge import StopBridge
from ..dto.responses import RecordingStopResponse, RecordingStopData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class StopService:
    """Service for stopping recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Stop Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = StopBridge(bridge_lib_path)
    
    async def stop_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> RecordingStopResponse:
        """
        Stop a recording.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to stop
            
        Returns:
            Recording stop response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.stop_recording(
                base_path=base_path,
                recording_id=recording_id
            )
            
            # Parse response
            if result.get("status") == "success":
                stop_data = result.get("data", {})
                
                # Convert timestamp from milliseconds to ISO string
                if isinstance(stop_data.get("endTime"), (int, float)):
                    from datetime import datetime
                    dt = datetime.fromtimestamp(stop_data["endTime"] / 1000)
                    stop_data["end_time"] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    stop_data.pop("endTime", None)
                
                # Map duration from seconds to milliseconds
                if "durationSec" in stop_data:
                    stop_data["duration"] = int(stop_data["durationSec"] * 1000)
                    stop_data.pop("durationSec", None)
                elif "duration_sec" in stop_data:
                    stop_data["duration"] = int(stop_data["duration_sec"] * 1000)
                    stop_data.pop("duration_sec", None)
                
                # Remove extra fields to match Node.js response
                stop_data.pop("status", None)
                stop_data.pop("message", None)
                
                data = RecordingStopData(**stop_data)
                
                return RecordingStopResponse(
                    status=ResponseStatus.SUCCESS,
                    message="Recording stopped",
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingStopResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to stop recording"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording stop operation failed: {e}")
