"""
Executor service implementation with modular architecture.

This module provides the main Executor class for managing pipeline execution
in the SW Registry Stack, using individual service classes for each operation.
"""

import asyncio
import json
import logging
from typing import Optional, Union, Dict, Any
from pathlib import Path
import sys

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.executor.dto import (
    ExecutorConfig,
    ExecutorCreateOptions,
    ExecutorListOptions,
    ExecutorHistoryOptions,
    ExecutorInfoOptions,
    ExecutorStartOptions,
    ExecutorStopOptions,
    ExecutorDestroyOptions,
    ExecutorVersionOptions,
    PipelineCreateResponse,
    PipelineCreateData,
    PipelineListResponse,
    PipelineListData,
    PipelineHistoryResponse,
    PipelineHistoryData,
    PipelineInfoResponse,
    PipelineStateTransitionResponse,
    PipelineStateTransitionData,
    ExecutorVersionResponse,
    ExecutorVersionData
)
from modules.executor.services import (
    CreateService,
    ListService,
    HistoryService,
    InfoService,
    StartService,
    StopService,
    DestroyService,
    VersionService
)
from shared.dto.common import CliResponse, ResponseStatus
from exceptions import (
    SdkError,
    ValidationError,
    ConfigurationError,
)
from modules.executor.utils.unified_logging import (
    unified_logging_service,
    LOG_LEVELS,
    LOG_SOURCES,
    UnifiedLoggingCallback
)

logger = logging.getLogger(__name__)


class Executor:
    """
    Main Executor class for managing pipeline execution.
    
    This class provides a high-level interface for all executor operations,
    delegating to individual service classes for modularity and maintainability.
    """
    
    def __init__(self, config: Union[ExecutorConfig, Dict[str, Any]]):
        """
        Initialize the Executor.
        
        Args:
            config: Executor configuration (ExecutorConfig object or dictionary)
        """
        try:
            if isinstance(config, dict):
                self.config = ExecutorConfig(**config)
            else:
                self.config = config
                
            self._is_initialized = False
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Executor: {e}")
        
        # Initialize individual services
        self._create_service = CreateService(self.config.bridge_lib_path)
        self._list_service = ListService(self.config.bridge_lib_path)
        self._history_service = HistoryService(self.config.bridge_lib_path)
        self._info_service = InfoService(self.config.bridge_lib_path)
        self._start_service = StartService(self.config.bridge_lib_path)
        self._stop_service = StopService(self.config.bridge_lib_path)
        self._destroy_service = DestroyService(self.config.bridge_lib_path)
        self._version_service = VersionService(self.config.bridge_lib_path)
    
    async def initialize(self) -> None:
        """Initialize the executor service."""
        if not self._is_initialized:
            # Initialize all services
            await asyncio.gather(
                self._create_service.initialize(),
                self._list_service.initialize(),
                self._history_service.initialize(),
                self._info_service.initialize(),
                self._start_service.initialize(),
                self._stop_service.initialize(),
                self._destroy_service.initialize(),
                self._version_service.initialize()
            )
            self._is_initialized = True
    
    async def create(
        self,
        options: ExecutorCreateOptions
    ) -> PipelineCreateResponse:
        """
        Create a pipeline.
        
        Args:
            options: Create options
            
        Returns:
            PipelineCreateResponse: Create response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        try:
            # Set up unified logging if enabled
            if hasattr(options, 'enable_logging') and options.enable_logging and hasattr(options, 'on_unified_log') and options.on_unified_log:
                unified_logging_service.add_callback(options.on_unified_log)
            
            # Log SDK operation
            unified_logging_service.log_sdk(
                'Executor',
                'create',
                'Starting pipeline creation',
                LOG_LEVELS.INFO,
                {
                    'base_path': self.config.base_path,
                    'device_id': getattr(options, 'device_id', None),
                    'has_json_file': bool(getattr(options, 'config', {}).get('json_file') if hasattr(options, 'config') else False),
                    'has_json_data': bool(getattr(options, 'config', {}).get('json_data') if hasattr(options, 'config') else False)
                }
            )
            
            result = await self._create_service.create_pipeline(
                base_path=self.config.base_path,
                options=options
            )
            
            # Set pipeline context for unified logging
            if result.status == ResponseStatus.SUCCESS and result.data:
                unified_logging_service.set_pipeline_context(
                    result.data.pipeline_id or '',
                    result.data.run_id or '',
                    result.data.device_id or ''
                )
                
                # Log successful creation
                unified_logging_service.log_pipeline(
                    'create',
                    'Pipeline created successfully',
                    LOG_LEVELS.INFO,
                    {
                        'pipeline_id': result.data.pipeline_id,
                        'run_id': result.data.run_id,
                        'device_id': result.data.device_id,
                        'background': getattr(options, 'config', {}).get('background', False) if hasattr(options, 'config') else False
                    }
                )
            
            return result
        except Exception as e:
            logger.error(f"Executor.create: error", {
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineCreateResponse(
                status=ResponseStatus.ERROR,
                message="Failed to create pipeline",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def list(
        self,
        options: ExecutorListOptions = None
    ) -> PipelineListResponse:
        """
        List pipeline instances.
        
        Args:
            options: List options
            
        Returns:
            PipelineListResponse: List response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if options is None:
            options = ExecutorListOptions()
        
        try:
            return await self._list_service.list_pipelines(
                base_path=self.config.base_path,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.list: error", {
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineListResponse(
                status=ResponseStatus.ERROR,
                message="Failed to list pipelines",
                data=PipelineListData(
                    pipelines=[],
                    total_count=0,
                    page=1,
                    page_size=0
                ),
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def history(
        self,
        options: ExecutorHistoryOptions = None
    ) -> PipelineHistoryResponse:
        """
        Get pipeline execution history.
        
        Args:
            options: History options
            
        Returns:
            PipelineHistoryResponse: History response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if options is None:
            options = ExecutorHistoryOptions()
        
        try:
            return await self._history_service.get_history(
                base_path=self.config.base_path,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.history: error", {
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineHistoryResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get pipeline history",
                data=PipelineHistoryData(
                    runs=[],
                    count=0
                ),
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def info(
        self,
        options: ExecutorInfoOptions
    ) -> PipelineInfoResponse:
        """
        Get pipeline information.
        
        Args:
            options: Info options
            
        Returns:
            PipelineInfoResponse: Info response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        try:
            return await self._info_service.get_info(
                base_path=self.config.base_path,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.info: error", {
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineInfoResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get pipeline info",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def start(
        self,
        run_id: str,
        options: ExecutorStartOptions = None
    ) -> PipelineStateTransitionResponse:
        """
        Start a pipeline instance.
        
        Args:
            run_id: Pipeline run ID
            options: Start options
            
        Returns:
            PipelineStateTransitionResponse: Start response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if not run_id or not run_id.strip():
            raise ValidationError("Run ID is required")
        
        if options is None:
            options = ExecutorStartOptions()
        
        try:
            return await self._start_service.start_pipeline(
                base_path=self.config.base_path,
                run_id=run_id,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.start: error", {
                "run_id": run_id,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return PipelineStateTransitionResponse(
                status=ResponseStatus.ERROR,
                message="Failed to start pipeline",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def stop(
        self,
        run_id: str,
        options: ExecutorStopOptions = None
    ) -> PipelineStateTransitionResponse:
        """
        Stop a pipeline instance.
        
        Args:
            run_id: Pipeline run ID
            options: Stop options
            
        Returns:
            PipelineStateTransitionResponse: Stop response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if not run_id or not run_id.strip():
            raise ValidationError("Run ID is required")
        
        if options is None:
            options = ExecutorStopOptions()
        
        try:
            return await self._stop_service.stop_pipeline(
                base_path=self.config.base_path,
                run_id=run_id,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.stop: error", {
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
    
    async def destroy(
        self,
        run_id: str,
        options: ExecutorDestroyOptions = None
    ) -> PipelineStateTransitionResponse:
        """
        Destroy a pipeline instance.
        
        Args:
            run_id: Pipeline run ID
            options: Destroy options
            
        Returns:
            PipelineStateTransitionResponse: Destroy response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if not run_id or not run_id.strip():
            raise ValidationError("Run ID is required")
        
        if options is None:
            options = ExecutorDestroyOptions()
        
        try:
            return await self._destroy_service.destroy_pipeline(
                base_path=self.config.base_path,
                run_id=run_id,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.destroy: error", {
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
    
    async def version(
        self,
        options: ExecutorVersionOptions = None
    ) -> ExecutorVersionResponse:
        """
        Get executor version information.
        
        Args:
            options: Version options
            
        Returns:
            ExecutorVersionResponse: Version response
        """
        if not self._is_initialized:
            raise SdkError("Executor not initialized. Call initialize() first.")
        
        if options is None:
            options = ExecutorVersionOptions()
        
        try:
            return await self._version_service.get_version(
                base_path=self.config.base_path,
                options=options
            )
        except Exception as e:
            logger.error(f"Executor.version: error", {
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return ExecutorVersionResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get executor version",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )
    
    async def close(self) -> None:
        """Close the executor service."""
        if self._is_initialized:
            # Close all services
            await asyncio.gather(
                self._create_service.close(),
                self._list_service.close(),
                self._history_service.close(),
                self._info_service.close(),
                self._start_service.close(),
                self._stop_service.close(),
                self._destroy_service.close(),
                self._version_service.close()
            )
            self._is_initialized = False