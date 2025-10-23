"""
History Service implementation for Executor operations.

This module provides the service layer for getting pipeline history,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorHistoryOptions, PipelineHistoryResponse, PipelineHistoryData, PipelineRun
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for getting pipeline history."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the History Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the history service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the history service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def get_history(
        self,
        base_path: str,
        options: ExecutorHistoryOptions
    ) -> PipelineHistoryResponse:
        """
        Get pipeline history.
        
        Args:
            base_path: Base path for executor operations
            options: History options
            
        Returns:
            PipelineHistoryResponse: History response
        """
        try:
            logger.debug('getPipelineHistory: invoking bridge.history', {
                "base_path": base_path,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.get_history(
                base_path=base_path,
                pipeline_id=options.pipeline_id,
                status=options.status
            )
            
            logger.debug('getPipelineHistory: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            
            if response_data.get("status") == "success":
                data_dict = response_data.get("data", {})
                runs_list = data_dict.get("runs", [])
                
                # Convert to PipelineRun objects
                runs = []
                for run_data in runs_list:
                    run = PipelineRun(
                        created_at=run_data.get('created_at', 0),
                        device_id=run_data.get('device_id', ''),
                        pipeline_id=run_data.get('pipeline_id', ''),
                        pipeline_name=run_data.get('pipeline_name', ''),
                        pipeline_version=run_data.get('pipeline_version', ''),
                        process_id=run_data.get('process_id', -1),
                        run_id=run_data.get('run_id', ''),
                        status=run_data.get('status', '')
                    )
                    runs.append(run)
                
                # Create response data
                history_data = PipelineHistoryData(
                    runs=runs,
                    count=data_dict.get('count', len(runs))
                )
                
                return PipelineHistoryResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline history retrieved successfully"),
                    data=history_data
                )
            else:
                error_data = response_data.get("error", {})
                return PipelineHistoryResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to get pipeline history"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('getPipelineHistory: error', {
                "base_path": base_path,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineHistoryResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get pipeline history",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )