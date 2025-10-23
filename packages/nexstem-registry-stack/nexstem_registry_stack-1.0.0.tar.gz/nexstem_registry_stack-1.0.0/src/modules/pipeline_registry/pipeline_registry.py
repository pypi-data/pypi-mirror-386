"""
Pipeline Registry service implementation.

This module provides the main PipelineRegistry class for managing pipelines
in the SW Registry Stack.
"""

import asyncio
from typing import Optional, Union, Dict, Any
from .dto import (
    PipelineRegistryConfig,
    PipelineListOptions,
    PipelineInfoOptions,
    PipelinePushOptions,
    PipelinePullOptions,
    PipelineRemoveOptions,
    PipelineStatusOptions,
    PipelineListResponse,
    PipelineInfoResponse,
    PipelinePushResponse,
    PipelinePullResponse,
    PipelineRemoveResponse,
    PipelineStatusResponse,
    Pipeline,
    PipelineListData,
    PipelineInfo,
    PipelineInstallData,
    PipelineRemoveData,
    PipelinePushData,
    PipelinePullData,
    PipelineStatusData,
)
from .bridge import PipelineRegistryBridge
from exceptions import (
    SdkError,
    ValidationError,
    FfiBridgeError,
    ConfigurationError,
)
from shared.dto.common import ResponseStatus


class PipelineRegistry:
    """Main Pipeline Registry service class."""
    
    def __init__(self, config: Union[PipelineRegistryConfig, Dict[str, Any]]):
        """
        Initialize the Pipeline Registry.
        
        Args:
            config: Configuration for the Pipeline Registry
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            if isinstance(config, dict):
                self.config = PipelineRegistryConfig(**config)
            else:
                self.config = config
                
            self.bridge = PipelineRegistryBridge(self.config.bridge_lib_path)
            self._is_initialized = False
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Pipeline Registry: {e}")
    
    async def initialize(self) -> None:
        """
        Initialize the Pipeline Registry bridge.
        
        Raises:
            FfiBridgeError: If bridge initialization fails
        """
        try:
            self.bridge.load()
            self._is_initialized = True
        except Exception as e:
            raise FfiBridgeError(f"Failed to initialize Pipeline Registry bridge: {e}")
    
    async def close(self) -> None:
        """
        Close the Pipeline Registry bridge.
        
        Raises:
            FfiBridgeError: If bridge cleanup fails
        """
        try:
            if self._is_initialized:
                self.bridge.unload()
                self._is_initialized = False
        except Exception as e:
            raise FfiBridgeError(f"Failed to close Pipeline Registry bridge: {e}")
    
    async def list(
        self, 
        options: Optional[PipelineListOptions] = None
    ) -> PipelineListResponse:
        """
        List pipelines.
        
        Args:
            options: Options for listing pipelines
            
        Returns:
            Pipeline list response
            
        Raises:
            ValidationError: If validation fails
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if options is None:
                options = PipelineListOptions()
            
            # Validate options
            if options.page and options.page < 1:
                raise ValidationError("Page must be >= 1")
            if options.page_size and options.page_size < 1:
                raise ValidationError("Page size must be >= 1")
            
            # Call bridge
            if options.remote or options.pipeline or options.versions or options.page or options.page_size:
                result = await self.bridge.list_pipelines_with_options(
                    base_path=self.config.base_path,
                    remote=options.remote or False,
                    page=options.page or 1,
                    page_size=options.page_size or 10,
                    pipeline_id=options.pipeline,
                    versions=options.versions or False
                )
            else:
                result = await self.bridge.list_pipelines(self.config.base_path)
            
            # Parse response
            if result.get("status") == "success":
                data = PipelineListData(**result.get("data", {}))
                return PipelineListResponse(
                    data=data,
                    error=None,
                    message=result.get("message", "Pipelines listed successfully"),
                    status="success"
                )
            else:
                return PipelineListResponse(
                    data=None,
                    error=result.get("error"),
                    message=result.get("message", "Failed to list pipelines"),
                    status="error"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise FfiBridgeError(f"Pipeline list operation failed: {e}")
    
    async def info(
        self,
        pipeline_id_version: str,
        options: Optional[PipelineInfoOptions] = None
    ) -> PipelineInfoResponse:
        """
        Get pipeline information.
        
        Args:
            pipeline_id_version: Pipeline ID and version in format "id@version"
            options: Options for getting pipeline info
            
        Returns:
            Pipeline info response
            
        Raises:
            ValidationError: If validation fails
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if options is None:
                options = PipelineInfoOptions()
            
            # Parse pipeline ID and version
            if "@" not in pipeline_id_version:
                raise ValidationError("Pipeline ID must be in format 'id@version'")
            
            pipeline_id, version = pipeline_id_version.split("@", 1)
            if not pipeline_id or not version:
                raise ValidationError("Pipeline ID and version cannot be empty")
            
            # Call bridge
            result = await self.bridge.get_pipeline_info(
                base_path=self.config.base_path,
                pipeline_id=pipeline_id,
                version=version,
                remote=options.remote or False,
                extend=options.extend or False
            )
            
            # Parse response
            if result.get("status") == "success":
                data = PipelineInfo(**result.get("data", {}))
                return PipelineInfoResponse(
                    data=data,
                    error=None,
                    message=result.get("message", "Pipeline info retrieved successfully"),
                    status="success"
                )
            else:
                return PipelineInfoResponse(
                    data=None,
                    error=result.get("error"),
                    message=result.get("message", "Failed to get pipeline info"),
                    status="error"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise FfiBridgeError(f"Pipeline info operation failed: {e}")
    
    async def install(
        self,
        pipeline_id_version: str,
        options: Optional[PipelinePullOptions] = None
    ) -> PipelinePullResponse:
        """
        Install (pull) a pipeline.
        
        Args:
            pipeline_id_version: Pipeline ID and version in format "id@version"
            options: Options for installing pipeline
            
        Returns:
            Pipeline install response
            
        Raises:
            ValidationError: If validation fails
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if options is None:
                options = PipelinePullOptions()
            
            # Parse pipeline ID and version
            if "@" not in pipeline_id_version:
                raise ValidationError("Pipeline ID must be in format 'id@version'")
            
            pipeline_id, version = pipeline_id_version.split("@", 1)
            if not pipeline_id or not version:
                raise ValidationError("Pipeline ID and version cannot be empty")
            
            # Call bridge
            result = await self.bridge.install_pipeline(
                base_path=self.config.base_path,
                pipeline_id=pipeline_id,
                version=version,
                force=options.force or False
            )
            
            # Parse response
            if result.get("status") == "success":
                data = PipelinePullData(**result.get("data", {}))
                return PipelinePullResponse(
                    data=data,
                    error=None,
                    message=result.get("message", "Pipeline installed successfully"),
                    status="success"
                )
            else:
                # Handle error case - data might be None or empty
                data_dict = result.get("data", {})
                if data_dict:
                    data = PipelinePullData(**data_dict)
                else:
                    data = None
                
                return PipelinePullResponse(
                    data=data,
                    error=result.get("error"),
                    message=result.get("message", "Failed to install pipeline"),
                    status="error"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise FfiBridgeError(f"Pipeline install operation failed: {e}")
    
    async def remove(
        self,
        pipeline_id_version: str,
        options: Optional[PipelineRemoveOptions] = None
    ) -> PipelineRemoveResponse:
        """
        Remove a pipeline.
        
        Args:
            pipeline_id_version: Pipeline ID and version in format "id@version"
            options: Options for removing pipeline
            
        Returns:
            Pipeline remove response
            
        Raises:
            ValidationError: If validation fails
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if options is None:
                options = PipelineRemoveOptions()
            
            # Parse pipeline ID and version
            if "@" not in pipeline_id_version:
                raise ValidationError("Pipeline ID must be in format 'id@version'")
            
            pipeline_id, version = pipeline_id_version.split("@", 1)
            if not pipeline_id or not version:
                raise ValidationError("Pipeline ID and version cannot be empty")
            
            # Call bridge
            result = await self.bridge.uninstall_pipeline(
                base_path=self.config.base_path,
                pipeline_id=pipeline_id,
                version=version
            )
            
            # Parse response
            if result.get("status") == "success":
                data = PipelineRemoveData(**result.get("data", {}))
                return PipelineRemoveResponse(
                    data=data,
                    error=None,
                    message=result.get("message", "Pipeline removed successfully"),
                    status="success"
                )
            else:
                # Handle error case - data might be None or empty
                data_dict = result.get("data", {})
                if data_dict:
                    data = PipelineRemoveData(**data_dict)
                else:
                    data = None
                
                return PipelineRemoveResponse(
                    data=data,
                    error=result.get("error"),
                    message=result.get("message", "Failed to remove pipeline"),
                    status="error"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise FfiBridgeError(f"Pipeline remove operation failed: {e}")
    
    async def push(
        self,
        pipeline_id_version: str,
        tar_path: str,
        options: Optional[PipelinePushOptions] = None
    ) -> PipelinePushResponse:
        """
        Push a pipeline.
        
        Args:
            pipeline_id_version: Pipeline ID and version in format "id@version"
            tar_path: Path to the pipeline tar file
            options: Options for pushing pipeline
            
        Returns:
            Pipeline push response
            
        Raises:
            ValidationError: If validation fails
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            if options is None:
                options = PipelinePushOptions()
            
            # Parse pipeline ID and version
            if "@" not in pipeline_id_version:
                raise ValidationError("Pipeline ID must be in format 'id@version'")
            
            pipeline_id, version = pipeline_id_version.split("@", 1)
            if not pipeline_id or not version:
                raise ValidationError("Pipeline ID and version cannot be empty")
            
            if not tar_path:
                raise ValidationError("Tar path cannot be empty")
            
            # Call bridge
            result = await self.bridge.push_pipeline(
                base_path=self.config.base_path,
                pipeline_id=pipeline_id,
                version=version,
                tar_path=tar_path,
                local_only=options.local or False
            )
            
            # Parse response
            if result.get("status") == "success":
                data = PipelinePushData(**result.get("data", {}))
                return PipelinePushResponse(
                    status=ResponseStatus.SUCCESS,
                    message=result.get("message", "Pipeline pushed successfully"),
                    data=data
                )
            else:
                return PipelinePushResponse(
                    status=ResponseStatus.ERROR,
                    message=result.get("message", "Failed to push pipeline"),
                    data=None,
                    error=result.get("error")
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise FfiBridgeError(f"Pipeline push operation failed: {e}")
    
    async def status(self) -> PipelineStatusResponse:
        """
        Get pipeline registry status.
        
        Returns:
            Pipeline status response
            
        Raises:
            FfiBridgeError: If bridge operation fails
        """
        if not self._is_initialized:
            await self.initialize()
        
        try:
            # For now, we'll use a simple status check
            # This could be enhanced to check actual registry status
            return PipelineStatusResponse(
                status=ResponseStatus.SUCCESS,
                message="Pipeline registry is operational",
                data=PipelineStatusData(
                    id="registry",
                    version="1.0.0",
                    status="operational"
                )
            )
                
        except Exception as e:
            raise FfiBridgeError(f"Pipeline status operation failed: {e}")
    
    def get_config(self) -> PipelineRegistryConfig:
        """
        Get the current configuration.
        
        Returns:
            Current configuration
        """
        return self.config
    
    def update_config(self, config: Union[PipelineRegistryConfig, Dict[str, Any]]) -> None:
        """
        Update the configuration.
        
        Args:
            config: New configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            if isinstance(config, dict):
                self.config = PipelineRegistryConfig(**config)
            else:
                self.config = config
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {e}")
