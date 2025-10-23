"""
Download Service implementation for Recorder operations.

This module provides the service layer for downloading recordings,
handling business logic and data transformation.
"""

from typing import Dict, Any
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.download_bridge import DownloadBridge
from ..dto.responses import RecordingDownloadResponse, RecordingDownloadData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError


class DownloadService:
    """Service for downloading recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Download Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = DownloadBridge(bridge_lib_path)
    
    async def download_recording(
        self,
        base_path: str,
        recording_id: str,
        destination: str
    ) -> RecordingDownloadResponse:
        """
        Download a recording.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to download
            destination: Destination path for download
            
        Returns:
            Recording download response
            
        Raises:
            FfiBridgeError: If the operation fails
        """
        try:
            # Call bridge
            result = await self.bridge.download_recording(
                base_path=base_path,
                recording_id=recording_id,
                destination=destination
            )
            
            # Parse response
            if result.get("status") == "success":
                download_data = result.get("data", {})
                
                # Map field names to match expected structure
                if "recordingId" in download_data:
                    download_data["id"] = download_data.pop("recordingId")
                
                # Ensure sourcePath is present (Node.js includes this)
                if "sourcePath" not in download_data and "source_path" not in download_data:
                    # If not provided by bridge, we might need to derive it
                    # For now, assume the bridge provides it
                    pass
                
                data = RecordingDownloadData(**download_data)
                
                return RecordingDownloadResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Recording downloaded successfully"),
                    data=data
                )
            else:
                error_data = result.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return RecordingDownloadResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to download recording"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            raise FfiBridgeError(f"Recording download operation failed: {e}")
