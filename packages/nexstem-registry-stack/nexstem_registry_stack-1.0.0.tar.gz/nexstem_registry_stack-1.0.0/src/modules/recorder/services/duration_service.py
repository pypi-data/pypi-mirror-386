"""
Duration Service implementation for Recorder operations.

This module provides the service layer for getting total duration,
handling business logic and data transformation.
"""

from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.duration_bridge import DurationBridge
from ..dto.responses import RecordingTotalDurationResponse, RecordingTotalDurationData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class DurationService:
    """Service for getting total duration."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Duration Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = DurationBridge(bridge_lib_path)
    
    async def get_total_duration(
        self,
        base_path: str
    ) -> RecordingTotalDurationResponse:
        """
        Get total duration of all recordings.
        
        Args:
            base_path: Base path for recording storage
            
        Returns:
            Recording total duration response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.get_total_duration(
                base_path=base_path
            )
            
            # Parse response
            if result.get("status") == "success":
                duration_data = result.get("data", {})
                
                # Map field names to match expected structure
                if "totalDurationSeconds" in duration_data:
                    duration_data["totalDurationSec"] = duration_data.pop("totalDurationSeconds")
                
                data = RecordingTotalDurationData(**duration_data)
                
                return RecordingTotalDurationResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Total duration computed"),
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingTotalDurationResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to get total duration"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording total duration operation failed: {e}")
