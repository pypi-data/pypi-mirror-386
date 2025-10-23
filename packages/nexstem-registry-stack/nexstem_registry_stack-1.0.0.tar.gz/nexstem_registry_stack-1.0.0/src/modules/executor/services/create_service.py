"""
Create Service implementation for Executor operations.

This module provides the service layer for creating pipelines,
handling business logic and data transformation.
"""

import json
import logging
import time
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorCreateOptions, PipelineCreateResponse, PipelineCreateData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class CreateService:
    """Service for creating pipelines."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Create Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the create service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the create service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def create_pipeline(
        self,
        base_path: str,
        options: ExecutorCreateOptions
    ) -> PipelineCreateResponse:
        """
        Create a pipeline.
        
        Args:
            base_path: Base path for executor operations
            options: Create options
            
        Returns:
            PipelineCreateResponse: Create response
        """
        try:
            logger.debug('createPipeline: invoking bridge.create', {
                "base_path": base_path,
                "options": options.model_dump() if options else None
            })
            
            # Prepare configuration
            config_overrides = None
            if options.config:
                config_overrides = json.dumps(options.config)
            
            # Determine input method
            json_file = None
            json_data = None
            
            if options.config:
                if 'jsonFile' in options.config:
                    json_file = options.config['jsonFile']
                elif 'jsonData' in options.config:
                    json_data = options.config['jsonData']
            
            # Create logging callback if enabled
            log_callback = None
            if hasattr(options, 'enable_logging') and options.enable_logging and hasattr(options, 'on_unified_log') and options.on_unified_log:
                def create_log_callback(unified_callback):
                    def c_log_callback(node_id, level, message, json_data):
                        try:
                            # Convert to unified log entry
                            from modules.executor.utils.unified_logging import UnifiedLogEntry, LOG_LEVELS, LOG_SOURCES
                            import json as json_lib
                            
                            # Parse JSON data if provided
                            data = {}
                            if json_data:
                                try:
                                    data = json_lib.loads(json_data)
                                except:
                                    data = {"raw": json_data}
                            
                            # Create unified log entry
                            entry = UnifiedLogEntry(
                                node_id=node_id or "",
                                pipeline_id="",  # Will be filled by unified logging service
                                run_id="",      # Will be filled by unified logging service
                                device_id=options.device_id or "",
                                level=int(level) if level.isdigit() else LOG_LEVELS.INFO,
                                source=LOG_SOURCES.NODE,
                                message=message or "",
                                timestamp=int(time.time() * 1000),
                                elapsed_ms=0,  # Will be calculated by unified logging service
                                function_name="",
                                file_name="",
                                line_number=0,
                                data=data,
                                metadata={}
                            )
                            
                            # Call the unified callback
                            unified_callback(entry)
                        except Exception as e:
                            logger.error(f"Error in unified logging callback: {e}")
                    
                    return c_log_callback
                
                log_callback = create_log_callback(options.on_unified_log)
            
            # Call the bridge
            json_response = await self.bridge.create_pipeline(
                base_path=base_path,
                json_file=json_file,
                json_data=json_data,
                device_id=options.device_id,
                background=options.background,
                config_overrides=config_overrides,
                log_callback=log_callback
            )
            
            logger.debug('createPipeline: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            if response_data.get("status") == "success":
                data_dict = response_data.get("data", {})
                
                # Create PipelineCreateData
                create_data = PipelineCreateData(
                    run_id=data_dict.get("run_id", ""),
                    pipeline_id=data_dict.get("pipeline_id", ""),
                    device_id=data_dict.get("device_id"),
                    process_id=data_dict.get("process_id"),
                    state=data_dict.get("state", ""),
                    background=data_dict.get("background", True),
                    created_at=data_dict.get("created_at", 0)
                )
                
                return PipelineCreateResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Pipeline created successfully"),
                    data=create_data
                )
            else:
                error_data = response_data.get("error", {})
                if isinstance(error_data, dict) and "type" not in error_data:
                    error_data["type"] = "execution_error"
                
                return PipelineCreateResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to create pipeline"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('createPipeline: error', {
                "base_path": base_path,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineCreateResponse(
                status=ResponseStatus.ERROR,
                message="Failed to create pipeline",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )