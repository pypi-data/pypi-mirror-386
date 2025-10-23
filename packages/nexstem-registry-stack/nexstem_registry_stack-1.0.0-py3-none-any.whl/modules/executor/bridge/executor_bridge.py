"""
Executor Bridge implementation using CFFI.

This module provides the bridge layer for Executor operations,
handling the CFFI integration with the native C++ library.
"""

import json
import logging
from typing import Optional, Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class ExecutorBridge(BaseBridge):
    """Bridge for Executor operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Executor Bridge.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        super().__init__(
            library_path=bridge_lib_path,
            library_key="executor_bridge"
        )
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for executor operations."""
        self._ffi.cdef("""
            // Executor Bridge C Interface
            char* executor_bridge_create(
                const char* base_path,
                const char* json_file,
                const char* json_data,
                const char* device_id,
                int background,
                const char* config_overrides
            );
            
            char* executor_bridge_list(
                const char* base_path,
                const char* status_filter,
                const char* search_term
            );
            
            char* executor_bridge_history(
                const char* base_path,
                const char* pipeline_id,
                const char* status
            );
            
            char* executor_bridge_info(
                const char* base_path,
                const char* json_file,
                const char* json_data,
                const char* run_id
            );
            
            char* executor_bridge_start(
                const char* base_path,
                const char* run_id
            );
            
            char* executor_bridge_stop(
                const char* base_path,
                const char* run_id
            );
            
            char* executor_bridge_destroy(
                const char* base_path,
                const char* run_id
            );
            
            char* executor_bridge_version(
                const char* base_path
            );
            
            void executor_bridge_string_free(char* string_ptr);
        """)
    
    async def create_pipeline(
        self,
        base_path: str,
        json_file: Optional[str] = None,
        json_data: Optional[str] = None,
        device_id: Optional[str] = None,
        background: bool = True,
        config_overrides: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pipeline using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            json_file: Path to JSON file (optional)
            json_data: JSON data string (optional)
            device_id: Device ID (optional)
            background: Whether to run in background
            config_overrides: Configuration overrides JSON string (optional)
            
        Returns:
            Dictionary containing the create response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            json_file_bytes = json_file.encode('utf-8') if json_file else self._ffi.NULL
            json_data_bytes = json_data.encode('utf-8') if json_data else self._ffi.NULL
            device_id_bytes = device_id.encode('utf-8') if device_id else self._ffi.NULL
            config_overrides_bytes = config_overrides.encode('utf-8') if config_overrides else self._ffi.NULL
            
            result_ptr = self._lib.executor_bridge_create(
                base_path.encode('utf-8'),
                json_file_bytes,
                json_data_bytes,
                device_id_bytes,
                1 if background else 0,
                config_overrides_bytes
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to create pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline create operation failed: {e}")
    
    async def list_pipelines(
        self,
        base_path: str,
        status_filter: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List pipelines using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            status_filter: Filter by status (optional)
            search_term: Search term (optional)
            
        Returns:
            Dictionary containing the list response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            status_filter_bytes = status_filter.encode('utf-8') if status_filter else self._ffi.NULL
            search_term_bytes = search_term.encode('utf-8') if search_term else self._ffi.NULL
            
            result_ptr = self._lib.executor_bridge_list(
                base_path.encode('utf-8'),
                status_filter_bytes,
                search_term_bytes
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to list pipelines from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline list operation failed: {e}")
    
    async def get_history(
        self,
        base_path: str,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pipeline history using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            pipeline_id: Filter by pipeline ID (optional)
            status: Filter by status (optional)
            
        Returns:
            Dictionary containing the history response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            pipeline_id_bytes = pipeline_id.encode('utf-8') if pipeline_id else self._ffi.NULL
            status_bytes = status.encode('utf-8') if status else self._ffi.NULL
            
            result_ptr = self._lib.executor_bridge_history(
                base_path.encode('utf-8'),
                pipeline_id_bytes,
                status_bytes
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get pipeline history from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline history operation failed: {e}")
    
    async def get_info(
        self,
        base_path: str,
        json_file: Optional[str] = None,
        json_data: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pipeline info using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            json_file: Path to JSON file (optional)
            json_data: JSON data string (optional)
            run_id: Pipeline run ID (optional)
            
        Returns:
            Dictionary containing the info response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            json_file_bytes = json_file.encode('utf-8') if json_file else self._ffi.NULL
            json_data_bytes = json_data.encode('utf-8') if json_data else self._ffi.NULL
            run_id_bytes = run_id.encode('utf-8') if run_id else self._ffi.NULL
            
            result_ptr = self._lib.executor_bridge_info(
                base_path.encode('utf-8'),
                json_file_bytes,
                json_data_bytes,
                run_id_bytes
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get pipeline info from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline info operation failed: {e}")
    
    async def start_pipeline(
        self,
        base_path: str,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Start a pipeline using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            run_id: Pipeline run ID
            
        Returns:
            Dictionary containing the start response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.executor_bridge_start(
                base_path.encode('utf-8'),
                run_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to start pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline start operation failed: {e}")
    
    async def stop_pipeline(
        self,
        base_path: str,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Stop a pipeline using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            run_id: Pipeline run ID
            
        Returns:
            Dictionary containing the stop response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.executor_bridge_stop(
                base_path.encode('utf-8'),
                run_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to stop pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline stop operation failed: {e}")
    
    async def destroy_pipeline(
        self,
        base_path: str,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Destroy a pipeline using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            run_id: Pipeline run ID
            
        Returns:
            Dictionary containing the destroy response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.executor_bridge_destroy(
                base_path.encode('utf-8'),
                run_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to destroy pipeline from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline destroy operation failed: {e}")
    
    async def get_version(
        self,
        base_path: str
    ) -> Dict[str, Any]:
        """
        Get executor version using the native bridge.
        
        Args:
            base_path: Base path for executor operations
            
        Returns:
            Dictionary containing the version response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.executor_bridge_version(
                base_path.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get executor version from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Executor version operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """
        Free a C string returned by bridge functions.
        
        Args:
            string_ptr: Pointer to the C string to free
        """
        if string_ptr:
            self._lib.executor_bridge_string_free(string_ptr)