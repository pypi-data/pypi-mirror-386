"""
Low-level FFI calls for list operation.

This module provides the CFFI interface for listing pipeline instances,
handling the native library calls for list operations.
"""

import logging
from typing import Optional, Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class ListBridge(BaseBridge):
    """Bridge for list operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the List Bridge.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        super().__init__(bridge_lib_path, "executor_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for list operations."""
        self._ffi.cdef("""
            // List Bridge C Interface
            char* executor_bridge_list(
                const char* status_filter,
                const char* search_term,
                const char* working_dir
            );
            
            void executor_bridge_string_free(char* string_ptr);
        """)
    
    async def list_pipelines(
        self,
        status_filter: Optional[str] = None,
        search_term: Optional[str] = None,
        working_dir: str = "/tmp/executor"
    ) -> Dict[str, Any]:
        """
        List pipeline instances using the native bridge.
        
        Args:
            status_filter: Filter by pipeline status
            search_term: Search term for pipeline name or device ID
            working_dir: Working directory
            
        Returns:
            Dictionary containing the list response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            status_filter_bytes = status_filter.encode('utf-8') if status_filter else self._ffi.NULL
            search_term_bytes = search_term.encode('utf-8') if search_term else self._ffi.NULL
            
            result_ptr = self.lib.executor_bridge_list(
                status_filter_bytes,
                search_term_bytes,
                working_dir.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to list pipelines from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            import json
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline list operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """Free a string pointer returned by the native library."""
        try:
            if string_ptr:
                self.lib.executor_bridge_string_free(string_ptr)
        except Exception as e:
            logger.warning(f"Failed to free string pointer: {e}")
