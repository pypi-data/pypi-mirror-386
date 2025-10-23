"""
List Service implementation for Executor operations.

This module provides the service layer for listing pipelines,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorListOptions, PipelineListResponse, PipelineListData, PipelineRun
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class ListService:
    """Service for listing pipelines."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the List Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the list service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the list service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def list_pipelines(
        self,
        base_path: str,
        options: ExecutorListOptions
    ) -> PipelineListResponse:
        """
        List pipelines.
        
        Args:
            base_path: Base path for executor operations
            options: List options
            
        Returns:
            PipelineListResponse: List response
        """
        try:
            logger.debug('listPipelines: invoking bridge.list', {
                "base_path": base_path,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.list_pipelines(
                base_path=base_path,
                status_filter=options.status,
                search_term=options.search
            )
            
            logger.debug('listPipelines: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            
            if response_data.get("status") == "success":
                data_dict = response_data.get("data", {})
                pipelines_list = data_dict.get("pipelines", [])
                
                # Convert to PipelineRun objects
                pipelines = []
                for pipeline_data in pipelines_list:
                    pipeline = PipelineRun(
                        created_at=pipeline_data.get('created_at', 0),
                        device_id=pipeline_data.get('device_id', ''),
                        pipeline_id=pipeline_data.get('pipeline_id', ''),
                        pipeline_name=pipeline_data.get('pipeline_name', ''),
                        pipeline_version=pipeline_data.get('pipeline_version', ''),
                        process_id=pipeline_data.get('process_id', -1),
                        run_id=pipeline_data.get('run_id', ''),
                        status=pipeline_data.get('status', '')
                    )
                    pipelines.append(pipeline)
                
                # Create response data
                list_data = PipelineListData(
                    pipelines=pipelines,
                    count=data_dict.get('count', len(pipelines))
                )
                
                return PipelineListResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline list retrieved successfully"),
                    data=list_data
                )
            else:
                error_data = response_data.get("error", {})
                return PipelineListResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to list pipelines"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('listPipelines: error', {
                "base_path": base_path,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineListResponse(
                status=ResponseStatus.ERROR,
                message="Failed to list pipelines",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )