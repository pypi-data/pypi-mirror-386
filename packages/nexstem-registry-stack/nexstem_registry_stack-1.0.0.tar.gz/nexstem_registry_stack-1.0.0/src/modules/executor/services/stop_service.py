"""
Stop Service implementation for Executor operations.

This module provides the service layer for stopping pipelines,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorStopOptions, PipelineStateTransitionResponse, PipelineStateTransitionData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class StopService:
    """Service for stopping pipelines."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Stop Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the stop service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the stop service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def stop_pipeline(
        self,
        base_path: str,
        run_id: str,
        options: ExecutorStopOptions
    ) -> PipelineStateTransitionResponse:
        """
        Stop a pipeline.
        
        Args:
            base_path: Base path for executor operations
            run_id: Pipeline run ID
            options: Stop options
            
        Returns:
            PipelineStateTransitionResponse: Stop response
        """
        try:
            logger.debug('stopPipeline: invoking bridge.stop', {
                "base_path": base_path,
                "run_id": run_id,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.stop_pipeline(
                base_path=base_path,
                run_id=run_id
            )
            
            logger.debug('stopPipeline: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            
            if response_data.get("status") == "success":
                pipeline_data = response_data.get("data", {})
                
                # Create response data
                transition_data = PipelineStateTransitionData(
                    run_id=pipeline_data.get('run_id', run_id),
                    pipeline_id=pipeline_data.get('pipeline_id', ''),
                    current_state=pipeline_data.get('current_state', 'started'),
                    new_state=pipeline_data.get('new_state', 'stopped'),
                    timestamp=pipeline_data.get('timestamp'),
                    zmq_address=pipeline_data.get('zmq_address'),
                    action=pipeline_data.get('action'),
                    valid_states=pipeline_data.get('valid_states')
                )
                
                return PipelineStateTransitionResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline stopped successfully"),
                    data=transition_data
                )
            else:
                error_data = response_data.get("error", {})
                return PipelineStateTransitionResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to stop pipeline"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('stopPipeline: error', {
                "base_path": base_path,
                "run_id": run_id,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineStateTransitionResponse(
                status=ResponseStatus.ERROR,
                message="Failed to stop pipeline",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )