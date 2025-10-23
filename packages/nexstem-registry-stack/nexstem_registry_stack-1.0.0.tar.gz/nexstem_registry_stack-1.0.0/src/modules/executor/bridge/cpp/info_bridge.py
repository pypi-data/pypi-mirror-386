"""
Low-level FFI calls for info operation.

This module provides the CFFI interface for getting pipeline information,
handling the native library calls for info operations.
"""

import logging
from typing import Optional, Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class InfoBridge(BaseBridge):
    """Bridge for info operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Info Bridge.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        super().__init__(bridge_lib_path, "executor_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for info operations."""
        self._ffi.cdef("""
            // Info Bridge C Interface
            char* executor_bridge_info(
                const char* json_file,
                const char* json_data,
                const char* run_id,
                const char* working_dir
            );
            
            void executor_bridge_string_free(char* string_ptr);
        """)
    
    async def get_info(
        self,
        json_file: Optional[str] = None,
        json_data: Optional[str] = None,
        run_id: Optional[str] = None,
        working_dir: str = "/tmp/executor"
    ) -> Dict[str, Any]:
        """
        Get pipeline information using the native bridge.
        
        Args:
            json_file: Path to JSON file
            json_data: Inline JSON data
            run_id: Pipeline run ID
            working_dir: Working directory
            
        Returns:
            Dictionary containing the info response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            json_file_bytes = json_file.encode('utf-8') if json_file else self._ffi.NULL
            json_data_bytes = json_data.encode('utf-8') if json_data else self._ffi.NULL
            run_id_bytes = run_id.encode('utf-8') if run_id else self._ffi.NULL
            
            result_ptr = self.lib.executor_bridge_info(
                json_file_bytes,
                json_data_bytes,
                run_id_bytes,
                working_dir.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get info from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            import json
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Pipeline info operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """Free a string pointer returned by the native library."""
        try:
            if string_ptr:
                self.lib.executor_bridge_string_free(string_ptr)
        except Exception as e:
            logger.warning(f"Failed to free string pointer: {e}")
