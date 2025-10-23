"""
Recorder Bridge implementation using CFFI.

This module provides the bridge layer for Recorder operations,
handling the CFFI integration with the native C++ library.
"""

import json
from typing import Optional, Dict, Any, List
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.bridge.base_bridge import BaseBridge
from exceptions import FfiBridgeError


class RecorderBridge(BaseBridge):
    """Bridge for Recorder operations using CFFI."""
    
    def __init__(self, bridge_lib_path: str):
        """
        Initialize the Recorder Bridge.
        
        Args:
            bridge_lib_path: Path to the recorder bridge library
        """
        super().__init__(library_path=bridge_lib_path, library_key="recorder_bridge")
    
    def _define_functions(self) -> None:
        """Define the CFFI interface for recorder operations."""
        self._ffi.cdef("""
            // Recorder Bridge C Interface
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
            
            const char* recorder_bridge_create(
                const char* base_path,
                const char* json_data
            );
            
            const char* recorder_bridge_update(
                const char* base_path,
                const char* recording_id,
                const char* json_data
            );
            
            const char* recorder_bridge_info(
                const char* base_path,
                const char* recording_id
            );
            
            const char* recorder_bridge_download(
                const char* base_path,
                const char* recording_id,
                const char* destination
            );
            
            const char* recorder_bridge_delete(
                const char* base_path,
                const char* recording_id
            );
            
            const char* recorder_bridge_start(
                const char* base_path,
                const char* recording_id
            );
            
            const char* recorder_bridge_stop(
                const char* base_path,
                const char* recording_id
            );
            
            const char* recorder_bridge_total_duration(
                const char* base_path
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
    ) -> Dict[str, Any]:
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
    
    async def create_recording(
        self,
        base_path: str,
        json_data: str
    ) -> Dict[str, Any]:
        """
        Create a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            json_data: JSON string with recording data
            
        Returns:
            Dictionary containing the create response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_create(
                base_path.encode('utf-8'),
                json_data.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to create recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording create operation failed: {e}")
    
    async def update_recording(
        self,
        base_path: str,
        recording_id: str,
        json_data: str
    ) -> Dict[str, Any]:
        """
        Update a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to update
            json_data: JSON string with updated recording data
            
        Returns:
            Dictionary containing the update response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_update(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8'),
                json_data.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to update recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording update operation failed: {e}")
    
    async def get_recording_info(
        self,
        base_path: str,
        recording_id: str
    ) -> Dict[str, Any]:
        """
        Get recording information using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to get info for
            
        Returns:
            Dictionary containing the info response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_info(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to get recording info from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording info operation failed: {e}")
    
    async def download_recording(
        self,
        base_path: str,
        recording_id: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Download a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to download
            destination: Destination path for download
            
        Returns:
            Dictionary containing the download response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_download(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8'),
                destination.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to download recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording download operation failed: {e}")
    
    async def delete_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> Dict[str, Any]:
        """
        Delete a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to delete
            
        Returns:
            Dictionary containing the delete response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_delete(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to delete recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording delete operation failed: {e}")
    
    async def start_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> Dict[str, Any]:
        """
        Start a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to start
            
        Returns:
            Dictionary containing the start response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_start(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to start recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording start operation failed: {e}")
    
    async def stop_recording(
        self,
        base_path: str,
        recording_id: str
    ) -> Dict[str, Any]:
        """
        Stop a recording using the native bridge.
        
        Args:
            base_path: Base path for recording storage
            recording_id: Recording ID to stop
            
        Returns:
            Dictionary containing the stop response
            
        Raises:
            FfiBridgeError: If the FFI call fails
        """
        try:
            result_ptr = self._lib.recorder_bridge_stop(
                base_path.encode('utf-8'),
                recording_id.encode('utf-8')
            )
            
            if not result_ptr:
                raise FfiBridgeError("Failed to stop recording from bridge")
            
            result_str = self._ffi.string(result_ptr).decode('utf-8')
            self._free_string(result_ptr)
            
            return json.loads(result_str)
            
        except Exception as e:
            raise FfiBridgeError(f"Recording stop operation failed: {e}")
    
    async def get_total_duration(
        self,
        base_path: str
    ) -> Dict[str, Any]:
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
