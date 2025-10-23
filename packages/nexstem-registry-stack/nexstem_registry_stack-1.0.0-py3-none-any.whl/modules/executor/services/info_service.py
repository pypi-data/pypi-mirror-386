"""
Info Service implementation for Executor operations.

This module provides the service layer for getting pipeline information,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorInfoOptions, PipelineInfoResponse, PipelineRun
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class InfoService:
    """Service for getting pipeline information."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Info Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the info service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the info service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def get_info(
        self,
        base_path: str,
        options: ExecutorInfoOptions
    ) -> PipelineInfoResponse:
        """
        Get pipeline information.
        
        Args:
            base_path: Base path for executor operations
            options: Info options
            
        Returns:
            PipelineInfoResponse: Info response
        """
        try:
            logger.debug('getPipelineInfo: invoking bridge.info', {
                "base_path": base_path,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.get_info(
                base_path=base_path,
                json_file=options.json_file,
                json_data=options.json_data,
                run_id=options.run_id
            )
            
            logger.debug('getPipelineInfo: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            
            if response_data.get("status") == "success":
                pipeline_data = response_data.get("data")
                
                if pipeline_data is None:
                    return PipelineInfoResponse(
                        status=ResponseStatus.ERROR,
                        message=response_data.get("message", "Pipeline info not found"),
                        data=None,
                        error=response_data.get("error", {"message": "Pipeline info not found", "type": "not_found"})
                    )
                
                # Convert to PipelineRun object
                pipeline_run = PipelineRun(
                    created_at=pipeline_data.get('created_at', 0),
                    device_id=pipeline_data.get('device_id', ''),
                    pipeline_id=pipeline_data.get('pipeline_id', ''),
                    pipeline_name=pipeline_data.get('pipeline_name', ''),
                    pipeline_version=pipeline_data.get('pipeline_version', ''),
                    process_id=pipeline_data.get('process_id', -1),
                    run_id=pipeline_data.get('run_id', ''),
                    status=pipeline_data.get('status', '')
                )
                
                return PipelineInfoResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline info retrieved successfully"),
                    data=pipeline_run
                )
            else:
                error_data = response_data.get("error", {})
                return PipelineInfoResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to get pipeline info"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('getPipelineInfo: error', {
                "base_path": base_path,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineInfoResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get pipeline info",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )