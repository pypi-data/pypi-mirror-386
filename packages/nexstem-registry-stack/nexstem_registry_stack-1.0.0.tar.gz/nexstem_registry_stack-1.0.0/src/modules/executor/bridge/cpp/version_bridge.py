"""
Low-level FFI calls for version operation.

This module provides the CFFI interface for getting executor version information,
handling the native library calls for version operations.
"""

import logging
from typing import Dict, Any
from cffi import FFI
from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class VersionBridge(BaseBridge):
    """Bridge for version operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Version Bridge.
        
        Args:
            bridge_lib_path: Path to the executor bridge library
        """
        super().__init__(bridge_lib_path, "executor_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for version operations."""
        self._ffi.cdef("""
            // Version Bridge C Interface
            char* executor_bridge_version(
                const char* working_dir
            );
            
            void executor_bridge_string_free(char* string_ptr);
        """)
    
    async def get_version(
        self,
        working_dir: str = "/tmp/executor"
    ) -> Dict[str, Any]:
        """
        Get executor version information using the native bridge.
        
        Args:
            working_dir: Working directory
            
        Returns:
            Dictionary containing the version response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self.lib.executor_bridge_version(
                working_dir.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get version from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            import json
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Version operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """Free a string pointer returned by the native library."""
        try:
            if string_ptr:
                self.lib.executor_bridge_string_free(string_ptr)
        except Exception as e:
            logger.warning(f"Failed to free string pointer: {e}")
