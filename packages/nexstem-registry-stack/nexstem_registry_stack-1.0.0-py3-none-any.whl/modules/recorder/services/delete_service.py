"""
Delete Service implementation for Recorder operations.

This module provides the service layer for deleting recordings,
handling business logic and data transformation.
"""

from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.delete_bridge import DeleteBridge
from ..dto.responses import RecordingDeleteResponse, RecordingDeleteData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class DeleteService:
    """Service for deleting recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Delete Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = DeleteBridge(bridge_lib_path)
    
    async def delete_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> RecordingDeleteResponse:
        """
        Delete a recording.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to delete
            
        Returns:
            Recording delete response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.delete_recording(
                base_path=base_path,
                recording_id=recording_id
            )
            
            # Parse response
            if result.get("status") == "success":
                delete_data = result.get("data", {})
                
                # Map field names to match expected structure
                if "recordingId" in delete_data:
                    delete_data["id"] = delete_data.pop("recordingId")
                
                # Add deletedAt timestamp if not provided
                if "deleted_at" not in delete_data and "deletedAt" not in delete_data:
                    from datetime import datetime
                    delete_data["deletedAt"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                data = RecordingDeleteData(**delete_data)
                
                return RecordingDeleteResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Recording deleted successfully"),
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingDeleteResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to delete recording"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording delete operation failed: {e}")
