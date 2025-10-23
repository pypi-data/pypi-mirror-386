"""
Low-level FFI calls for history operation.

This module provides the CFFI interface for getting pipeline execution history,
handling the native library calls for history operations.
"""

import logging
from typing import Optional, Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class HistoryBridge(BaseBridge):
    """Bridge for history operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the History Bridge.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        super().__init__(bridge_lib_path, "executor_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for history operations."""
        self._ffi.cdef("""
            // History Bridge C Interface
            char* executor_bridge_history(
                const char* pipeline_id,
                const char* status,
                const char* working_dir
            );
            
            void executor_bridge_string_free(char* string_ptr);
        """)
    
    async def get_history(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        working_dir: str = "/tmp/executor"
    ) -> Dict[str, Any]:
        """
        Get pipeline execution history using the native bridge.
        
        Args:
            pipeline_id: Filter by pipeline ID
            status: Filter by status
            working_dir: Working directory
            
        Returns:
            Dictionary containing the history response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            pipeline_id_bytes = pipeline_id.encode('utf-8') if pipeline_id else self._ffi.NULL
            status_bytes = status.encode('utf-8') if status else self._ffi.NULL
            
            result_ptr = self.lib.executor_bridge_history(
                pipeline_id_bytes,
                status_bytes,
                working_dir.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get history from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            import json
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline history operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """Free a string pointer returned by the native library."""
        try:
            if string_ptr:
                self.lib.executor_bridge_string_free(string_ptr)
        except Exception as e:
            logger.warning(f"Failed to free string pointer: {e}")
