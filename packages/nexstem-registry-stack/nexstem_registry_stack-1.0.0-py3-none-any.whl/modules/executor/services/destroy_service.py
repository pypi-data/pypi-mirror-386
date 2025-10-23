"""
Destroy Service implementation for Executor operations.

This module provides the service layer for destroying pipelines,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorDestroyOptions, PipelineStateTransitionResponse, PipelineStateTransitionData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class DestroyService:
    """Service for destroying pipelines."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Destroy Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the destroy service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the destroy service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def destroy_pipeline(
        self,
        base_path: str,
        run_id: str,
        options: ExecutorDestroyOptions
    ) -> PipelineStateTransitionResponse:
        """
        Destroy a pipeline.
        
        Args:
            base_path: Base path for executor operations
            run_id: Pipeline run ID
            options: Destroy options
            
        Returns:
            PipelineStateTransitionResponse: Destroy response
        """
        try:
            logger.debug('destroyPipeline: invoking bridge.destroy', {
                "base_path": base_path,
                "run_id": run_id,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.destroy_pipeline(
                base_path=base_path,
                run_id=run_id
            )
            
            logger.debug('destroyPipeline: bridge response received', {
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
                    current_state=pipeline_data.get('current_state', 'stopped'),
                    new_state=pipeline_data.get('new_state', 'destroyed'),
                    timestamp=pipeline_data.get('timestamp'),
                    zmq_address=pipeline_data.get('zmq_address'),
                    action=pipeline_data.get('action'),
                    valid_states=pipeline_data.get('valid_states')
                )
                
                return PipelineStateTransitionResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline destroyed successfully"),
                    data=transition_data
                )
            else:
                error_data = response_data.get("error", {})
                return PipelineStateTransitionResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to destroy pipeline"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('destroyPipeline: error', {
                "base_path": base_path,
                "run_id": run_id,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineStateTransitionResponse(
                status=ResponseStatus.ERROR,
                message="Failed to destroy pipeline",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )