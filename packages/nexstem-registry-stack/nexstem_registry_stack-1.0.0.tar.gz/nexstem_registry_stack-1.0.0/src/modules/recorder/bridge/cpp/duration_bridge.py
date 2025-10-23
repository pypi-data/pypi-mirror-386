"""
Duration Bridge implementation for Recorder operations.

This module provides the bridge layer for getting total duration,
handling the CFFI integration with the native C++ library.
"""

import json
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError


class DurationBridge(BaseBridge):
    """Bridge for getting total duration using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Duration Bridge.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        super().__init__(library_path=bridge_lib_path, library_key="recorder_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for duration operations."""
        self._ffi.cdef("""
            const char* recorder_bridge_total_duration(
                const char* base_path
            );
            
            void recorder_bridge_string_free(const char* str);
        """)
    
    async def get_total_duration(
        self,
        base_path: str
    ) -> dict:
        """
        Get total duration of all recordings using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            
        Returns:
            Dictionary containing the total duration response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_total_duration(
                base_path.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get total duration from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording total duration operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """
        Free a C string returned by bridge functions.
        
        Args:
            string_ptr: Pointer to the C string to free
        """
        if string_ptr:
            self._lib.recorder_bridge_string_free(string_ptr)
