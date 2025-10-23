"""
Version Service implementation for Executor operations.

This module provides the service layer for getting executor version information,
handling business logic and data transformation.
"""

import json
import logging
from typing import Optional
from modules.executor.bridge import ExecutorBridge
from modules.executor.dto import ExecutorVersionOptions, ExecutorVersionResponse, ExecutorVersionData
from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class VersionService:
    """Service for getting executor version information."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Version Service.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        self.bridge = ExecutorBridge(bridge_lib_path)
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the version service."""
        if not self._is_initialized:
            self.bridge.load()
            self._is_initialized = True
    
    async def close(self) -> None:
        """Close the version service."""
        if self._is_initialized:
            self.bridge.unload()
            self._is_initialized = False
    
    async def get_version(
        self,
        base_path: str,
        options: ExecutorVersionOptions
    ) -> ExecutorVersionResponse:
        """
        Get executor version information.
        
        Args:
            base_path: Base path for executor operations
            options: Version options
            
        Returns:
            ExecutorVersionResponse: Version response
        """
        try:
            logger.debug('getExecutorVersion: invoking bridge.version', {
                "base_path": base_path,
                "options": options.model_dump() if options else None
            })
            
            # Call the bridge
            json_response = await self.bridge.get_version(
                base_path=base_path
            )
            
            logger.debug('getExecutorVersion: bridge response received', {
                "jsonLength": len(str(json_response)) if json_response else 0
            })
            
            # Parse the response
            response_data = json_response
            
            if response_data.get("status") == "success":
                version_data = response_data.get("data", {})
                
                # Create response data
                version_info = ExecutorVersionData(
                    name=version_data.get('name', 'Pipeline Executor CLI'),
                    version=version_data.get('version', '1.0.0')
                )
                
                return ExecutorVersionResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Version information retrieved."),
                    data=version_info
                )
            else:
                error_data = response_data.get("error", {})
                return ExecutorVersionResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Failed to get executor version"),
                    data=None,
                    error=error_data
                )
                
        except Exception as e:
            logger.error('getExecutorVersion: error', {
                "base_path": base_path,
                "options": options.model_dump() if options else None,
                "error": str(e)
            })
            return ExecutorVersionResponse(
                status=ResponseStatus.ERROR,
                message="Failed to get executor version",
                data=None,
                error={"message": str(e), "type": "execution_error"}
            )