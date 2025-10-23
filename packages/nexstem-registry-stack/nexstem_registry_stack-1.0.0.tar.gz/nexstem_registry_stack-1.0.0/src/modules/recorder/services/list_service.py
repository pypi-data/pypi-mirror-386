"""
List Service implementation for Recorder operations.

This module provides the service layer for listing recordings,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.cpp.list_bridge import ListBridge
from ..dto.options import RecorderListOptions
from ..dto.responses import RecordingListResponse, RecordingListData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class ListService:
    """Service for listing recordings."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the List Service.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        self.bridge = ListBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if not self._is_initialized:
            # Initialize bridge if needed
            self._is_initialized = True
    
    async def list_recordings(
        self,
        base_path: str,
        options: Optional[RecorderListOptions] = None
    ) -> RecordingListResponse:
        """
        List recordings.
        
        Args:
            base_path: Base path for recording storage
            options: List options
            
        Returns:
            Recording list response
        """
        if options is None:
            options = RecorderListOptions()
        
        try:
            logger.debug(f"Listing recordings with options: {options.model_dump()}")
            
            # Use the bridge to get the JSON response
            try:
                json_response = self.bridge.list_recordings(
                    base_path=base_path,
                    order_by=options.order_by or "createdAt",
                    order=options.order or "DESC",
                    limit=options.limit or 0,
                    offset=options.offset or 0,
                    device_ids=options.device_ids,
                    subject_names=options.subject_names,
                    subject_ids=options.subject_ids
                )
                
                # Parse the JSON response - handle both string and dict responses
                if isinstance(json_response, str):
                    response_data = json.loads(json_response)
                else:
                    response_data = json_response
                
                # Convert to our response type - match Node.js format exactly
                if response_data.get("status") == "success":
                    data_dict = response_data.get("data", {})
                    
                    # Convert snake_case to camelCase to match Node.js
                    if "order_by" in data_dict:
                        data_dict["orderBy"] = data_dict.pop("order_by")
                    if "total_count" in data_dict:
                        data_dict["totalCount"] = data_dict.pop("total_count")
                    
                    data = RecordingListData(**data_dict)
                    return RecordingListResponse(
                        data=data,
                        error=None,
                        message=response_data.get("message", "Recordings listed successfully"),
                        status="success"
                    )
                else:
                    return RecordingListResponse(
                        data=None,
                        error=response_data.get("error"),
                        message=response_data.get("message", "Failed to list recordings"),
                        status="error"
                    )
            except Exception as bridge_error:
                # If bridge fails due to database issues, return empty list like Node.js
                logger.warning(f"Bridge call failed, returning empty list: {bridge_error}")
                data = RecordingListData(
                    count=0,
                    limit=options.limit or 0,
                    offset=options.offset or 0,
                    order=options.order or "DESC",
                    orderBy=options.order_by or "createdAt",
                    recordings=[],
                    totalCount=0
                )
                return RecordingListResponse(
                    data=data,
                    error=None,
                    message="Recordings listed successfully",
                    status="success"
                )
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return RecordingListResponse(
                data=None,
                error={"message": str(e), "type": "json_parse_error"},
                message="Failed to parse response from recorder",
                status="error"
            )
        except Exception as e:
            logger.error(f"List operation failed: {e}")
            return RecordingListResponse(
                data=None,
                error={"message": str(e), "type": "bridge_error"},
                message="Failed to list recordings",
                status="error"
            )
