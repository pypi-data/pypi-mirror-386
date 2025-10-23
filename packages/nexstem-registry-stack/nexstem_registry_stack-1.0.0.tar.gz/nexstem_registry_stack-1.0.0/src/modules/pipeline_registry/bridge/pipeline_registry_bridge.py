"""
Pipeline Registry Bridge implementation using CFFI.

This module provides the bridge layer for Pipeline Registry operations,
handling the CFFI integration with the native C++ library.
"""

import json
from typing import Optional, Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError


class PipelineRegistryBridge(BaseBridge):
    """Bridge for Pipeline Registry operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Pipeline Registry Bridge.
        
        Args:
            bridge_lib_path: Path to the pipeline registry bridge library
        """
        super().__init__(
            library_path=bridge_lib_path,
            library_key="pipeline_registry_bridge"
        )
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for pipeline registry operations."""
        self._ffi.cdef("""
            // Pipeline Registry Bridge C Interface
            const char* pipeline_registry_bridge_list(const char* base_path);
            
            const char* pipeline_registry_bridge_list_with_options(
                const char* base_path, 
                int remote, 
                int page, 
                int page_size, 
                const char* pipeline_id, 
                int versions
            );
            
            const char* pipeline_registry_bridge_info(
                const char* base_path,
                int remote,
                const char* id,
                const char* version,
                int extend
            );
            
            const char* pipeline_registry_bridge_install(
                const char* base_path,
                const char* id,
                const char* version,
                int force
            );
            
            const char* pipeline_registry_bridge_uninstall(
                const char* base_path,
                const char* id,
                const char* version
            );
            
            const char* pipeline_registry_bridge_push(
                const char* base_path,
                const char* id,
                const char* version,
                const char* tar_path,
                int local_only
            );
            
            void pipeline_registry_bridge_string_free(const char* s);
        """)
    
    async def list_pipelines(self, base_path: str) -> Dict[str, Any]:
        """
        List pipelines using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            
        Returns:
            Dictionary containing the list response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.pipeline_registry_bridge_list(
                base_path.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get pipeline list from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline list operation failed: {e}")
    
    async def list_pipelines_with_options(
        self,
        base_path: str,
        remote: bool = False,
        page: int = 1,
        page_size: int = 10,
        pipeline_id: Optional[str] = None,
        versions: bool = False
    ) -> Dict[str, Any]:
        """
        List pipelines with options using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            remote: Whether to list remote pipelines
            page: Page number (1-based)
            page_size: Number of items per page
            pipeline_id: Filter by pipeline ID
            versions: Whether to list versions
            
        Returns:
            Dictionary containing the list response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            pipeline_id_bytes = pipeline_id.encode('utf-8') if pipeline_id else self._ffi.NULL
            
            result_ptr = self._lib.pipeline_registry_bridge_list_with_options(
                base_path.encode('utf-8'),
                1 if remote else 0,
                page,
                page_size,
                pipeline_id_bytes,
                1 if versions else 0
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get pipeline list with options from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline list with options operation failed: {e}")
    
    async def get_pipeline_info(
        self,
        base_path: str,
        pipeline_id: str,
        version: str,
        remote: bool = False,
        extend: bool = False
    ) -> Dict[str, Any]:
        """
        Get pipeline information using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            pipeline_id: Pipeline ID
            version: Pipeline version
            remote: Whether to get remote pipeline info
            extend: Whether to get extended information
            
        Returns:
            Dictionary containing the pipeline info response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.pipeline_registry_bridge_info(
                base_path.encode('utf-8'),
                1 if remote else 0,
                pipeline_id.encode('utf-8'),
                version.encode('utf-8'),
                1 if extend else 0
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get pipeline info from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline info operation failed: {e}")
    
    async def install_pipeline(
        self,
        base_path: str,
        pipeline_id: str,
        version: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Install a pipeline using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            pipeline_id: Pipeline ID
            version: Pipeline version
            force: Whether to force reinstall
            
        Returns:
            Dictionary containing the install response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.pipeline_registry_bridge_install(
                base_path.encode('utf-8'),
                pipeline_id.encode('utf-8'),
                version.encode('utf-8'),
                1 if force else 0
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to install pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline install operation failed: {e}")
    
    async def uninstall_pipeline(
        self,
        base_path: str,
        pipeline_id: str,
        version: str
    ) -> Dict[str, Any]:
        """
        Uninstall a pipeline using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            pipeline_id: Pipeline ID
            version: Pipeline version
            
        Returns:
            Dictionary containing the uninstall response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.pipeline_registry_bridge_uninstall(
                base_path.encode('utf-8'),
                pipeline_id.encode('utf-8'),
                version.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to uninstall pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline uninstall operation failed: {e}")
    
    async def push_pipeline(
        self,
        base_path: str,
        pipeline_id: str,
        version: str,
        tar_path: str,
        local_only: bool = False
    ) -> Dict[str, Any]:
        """
        Push a pipeline using the native bridge.
        
        Args:
            base_path: Base path for pipeline operations
            pipeline_id: Pipeline ID
            version: Pipeline version
            tar_path: Path to the tar file
            local_only: Whether to only register locally
            
        Returns:
            Dictionary containing the push response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.pipeline_registry_bridge_push(
                base_path.encode('utf-8'),
                pipeline_id.encode('utf-8'),
                version.encode('utf-8'),
                tar_path.encode('utf-8'),
                1 if local_only else 0
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to push pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline push operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """
        Free a C string returned by bridge functions.
        
        Args:
            string_ptr: Pointer to the C string to free
        """
        if string_ptr:
            self._lib.pipeline_registry_bridge_string_free(string_ptr)
