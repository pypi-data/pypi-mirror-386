"""
Create Service implementation for Recorder operations.

This module provides the service layer for creating recordings,
handling business logic and data transformation.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import ResponseStatus, ErrorDetails
from ..bridge.cpp.create_bridge import CreateBridge
from ..dto.options import RecorderCreateOptions
from ..dto.responses import RecordingCreateResponse, RecordingCreateData
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class CreateService:
    """Service for creating recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Create Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = CreateBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if not self._is_initialized:
            # Initialize bridge if needed
            self._is_initialized = True
    
    async def create_recording(
        self,
        base_path: str,
        options: RecorderCreateOptions
    ) -> RecordingCreateResponse:
        """
        Create a new recording.
        
        Args:
            base_path: Base path for recording storage
            options: Create options
            
        Returns:
            RecordingCreateResponse: Create response
        """
        try:
            logger.debug(f"Creating recording with options: {options.model_dump()}")
            
            # Prepare JSON data for the native bridge
            json_data = {
                "name": options.name,
                "filePath": options.file_path,
                "deviceId": options.device_id or "",
                "subject": json.dumps(options.subject or {}),
                "graph": options.graph or "",
                "channels": json.dumps(options.channels or []),
                "filters": json.dumps(options.filters or []),
                "markers": json.dumps(options.markers or []),
                "meta": json.dumps(options.meta or {})
            }
            
            # Use the bridge to create the recording
            try:
                json_response = await self.bridge.create_recording(
                    base_path=base_path,
                    json_data=json.dumps(json_data)
                )
            
                # Parse the JSON response - handle both string and dict responses
                if isinstance(json_response, str):
                    response_data = json.loads(json_response)
                else:
                    response_data = json_response
                
                # Convert to our response type - match Node.js format exactly
                if response_data.get("status") == "success":
                    data_dict = response_data.get("data", {})
                    
                    # Parse JSON string fields to objects to match Node.js
                    if isinstance(data_dict.get("subject"), str):
                        try:
                            data_dict["subject"] = json.loads(data_dict["subject"])
                        except json.JSONDecodeError:
                            data_dict["subject"] = {}
                    
                    if isinstance(data_dict.get("channels"), str):
                        try:
                            data_dict["channels"] = json.loads(data_dict["channels"])
                        except json.JSONDecodeError:
                            data_dict["channels"] = []
                    
                    if isinstance(data_dict.get("filters"), str):
                        try:
                            data_dict["filters"] = json.loads(data_dict["filters"])
                        except json.JSONDecodeError:
                            data_dict["filters"] = []
                    
                    if isinstance(data_dict.get("markers"), str):
                        try:
                            data_dict["markers"] = json.loads(data_dict["markers"])
                        except json.JSONDecodeError:
                            data_dict["markers"] = []
                    
                    if isinstance(data_dict.get("meta"), str):
                        try:
                            data_dict["meta"] = json.loads(data_dict["meta"])
                        except json.JSONDecodeError:
                            data_dict["meta"] = {}
                    
                    # Convert timestamp milliseconds to formatted strings
                    if isinstance(data_dict.get("created_at"), (int, float)):
                        data_dict["createdAt"] = self._format_timestamp(data_dict.pop("created_at"))
                    if isinstance(data_dict.get("updated_at"), (int, float)):
                        data_dict["updatedAt"] = self._format_timestamp(data_dict.pop("updated_at"))
                    
                    data = RecordingCreateData(**data_dict)
                    return RecordingCreateResponse(
                        data=data,
                        error=None,
                        message=response_data.get("message", "Recording created successfully"),
                        status="success"
                    )
                else:
                    return RecordingCreateResponse(
                        data=None,
                        error=response_data.get("error"),
                        message=response_data.get("message", "Failed to create recording"),
                        status="error"
                    )
                    
            except Exception as bridge_error:
                # If bridge fails due to database issues, return error like Node.js
                logger.warning(f"Bridge call failed: {bridge_error}")
                return RecordingCreateResponse(
                    data=None,
                    error={"message": str(bridge_error), "type": "bridge_error"},
                    message="Failed to create recording",
                    status="error"
                )
                
        except Exception as error:
            logger.error(f"Create recording failed: {error}")
            return RecordingCreateResponse(
                data=None,
                error={"message": str(error), "type": "execution_error"},
                message="Failed to create recording",
                status="error"
            )
    
    def _format_timestamp(self, timestamp_ms: float) -> str:
        """Format timestamp from milliseconds to ISO string format."""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

