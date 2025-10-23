"""
List Bridge implementation for Recorder operations.

This module provides the bridge layer for listing recordings,
handling the CFFI integration with the native C++ library.
"""

import json
from typing import Optional, List
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError


class ListBridge(BaseBridge):
    """Bridge for listing recordings using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the List Bridge.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        super().__init__(library_path=bridge_lib_path, library_key="recorder_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for list operations."""
        self._ffi.cdef("""
            const char* recorder_bridge_list(
                const char* base_path,
                const char* order_by,
                const char* order,
                int limit,
                int offset,
                const char* device_ids,
                const char* subject_names,
                const char* subject_ids
            );
            
            void recorder_bridge_string_free(const char* str);
        """)
    
    def list_recordings(
        self,
        base_path: str,
        order_by: str = "createdAt",
        order: str = "DESC",
        limit: int = 0,
        offset: int = 0,
        device_ids: Optional[List[str]] = None,
        subject_names: Optional[List[str]] = None,
        subject_ids: Optional[List[str]] = None
    ) -> dict:
        """
        List recordings using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            order_by: Field to order by
            order: Order direction
            limit: Maximum number of recordings to return
            offset: Number of recordings to skip
            device_ids: List of device IDs to filter by
            subject_names: List of subject names to filter by
            subject_ids: List of subject IDs to filter by
            
        Returns:
            Dictionary containing the list response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            device_ids_str = ",".join(device_ids) if device_ids else ""
            subject_names_str = ",".join(subject_names) if subject_names else ""
            subject_ids_str = ",".join(subject_ids) if subject_ids else ""
            
            result_ptr = self._lib.recorder_bridge_list(
                base_path.encode('utf-8'),
                order_by.encode('utf-8'),
                order.encode('utf-8'),
                limit,
                offset,
                device_ids_str.encode('utf-8'),
                subject_names_str.encode('utf-8'),
                subject_ids_str.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to list recordings from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording list operation failed: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """
        Free a C string returned by bridge functions.
        
        Args:
            string_ptr: Pointer to the C string to free
        """
        if string_ptr:
            self._lib.recorder_bridge_string_free(string_ptr)
