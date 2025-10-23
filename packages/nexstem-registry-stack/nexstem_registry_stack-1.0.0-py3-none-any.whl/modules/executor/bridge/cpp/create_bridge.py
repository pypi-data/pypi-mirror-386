"""
Create bridge implementation for Executor operations.

This module provides the bridge class for creating pipelines,
handling FFI communication with the native executor bridge library.
"""

import ctypes
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ..base_bridge import BaseExecutorBridge
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class CreateBridge(BaseExecutorBridge):
    """Bridge for creating pipelines."""
    
    def __init__(self, library_path: str):
        """
        Initialize the Create Bridge.
        
        Args:
            library_path: Path to the executor bridge library
        """
        super().__init__(library_path, "executor_bridge")
        self._create_func = None
    
    def _setup_function_signatures(self) -> None:
        """Set up function signatures for the create bridge."""
        super()._setup_function_signatures()
        
        if not self._library:
            return
        
        try:
            # Get the create function
            self._create_func = getattr(self._library, 'executor_bridge_create', None)
            if not self._create_func:
                raise FfiBridgeError("executor_bridge_create function not found in library")
            
            # Set up function signature
            # executor_bridge_create(jsonFile, jsonData, deviceId, background, configOverrides, workingDir, logCallback) -> char*
            self._create_func.argtypes = [
                ctypes.c_char_p,  # jsonFile
                ctypes.c_char_p,  # jsonData
                ctypes.c_char_p,  # deviceId
                ctypes.c_int,     # background
                ctypes.c_char_p,  # configOverrides
                ctypes.c_char_p,  # workingDir
                ctypes.c_void_p   # logCallback (function pointer)
            ]
            self._create_func.restype = ctypes.c_char_p
            
            logger.debug("CreateBridge._setup_function_signatures: function signatures set up")
            
        except Exception as e:
            logger.error("CreateBridge._setup_function_signatures: failed to set up function signatures", {
                "error": str(e)
            })
            raise FfiBridgeError(f"Failed to set up create function signatures: {e}")
    
    async def create_pipeline(
        self,
        base_path: str,
        json_file: Optional[str] = None,
        json_data: Optional[str] = None,
        device_id: Optional[str] = None,
        background: bool = True,
        config_overrides: Optional[str] = None,
        log_callback: Optional[callable] = None
    ) -> str:
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
            JSON response string from the native function
        """
        if not self._is_initialized:
            raise FfiBridgeError("Bridge not initialized")
        
        try:
            logger.debug("CreateBridge.create_pipeline: invoking native call", {
                "basePath": base_path,
                "jsonFile": json_file,
                "hasJsonData": json_data is not None,
                "deviceId": device_id,
                "background": background,
                "hasConfigOverrides": config_overrides is not None
            })
            
            # Prepare arguments
            json_file_bytes = json_file.encode('utf-8') if json_file else b""
            json_data_bytes = json_data.encode('utf-8') if json_data else b""
            device_id_bytes = device_id.encode('utf-8') if device_id else b""
            config_overrides_bytes = config_overrides.encode('utf-8') if config_overrides else b""
            base_path_bytes = base_path.encode('utf-8') if base_path else b""
            
            # Create callback function if provided
            callback_ptr = None
            if log_callback:
                # Define the callback function type
                CALLBACK_FUNC = ctypes.CFUNCTYPE(
                    None,  # return type
                    ctypes.c_char_p,  # node_id
                    ctypes.c_char_p,  # level
                    ctypes.c_char_p,  # message
                    ctypes.c_char_p   # json_data
                )
                
                def c_callback(node_id, level, message, json_data):
                    try:
                        # Convert C strings to Python strings
                        node_id_str = node_id.decode('utf-8') if node_id else ""
                        level_str = level.decode('utf-8') if level else ""
                        message_str = message.decode('utf-8') if message else ""
                        json_data_str = json_data.decode('utf-8') if json_data else ""
                        
                        # Call the Python callback
                        log_callback(node_id_str, level_str, message_str, json_data_str)
                    except Exception as e:
                        logger.error(f"Error in logging callback: {e}")
                
                callback_ptr = CALLBACK_FUNC(c_callback)
            
            # Call the native function
            result_ptr = self._create_func(
                json_file_bytes,
                json_data_bytes,
                device_id_bytes,
                1 if background else 0,
                config_overrides_bytes,
                base_path_bytes,
                callback_ptr
            )
            
            if not result_ptr:
                raise FfiBridgeError("Native function returned null pointer")
            
            # Convert result to string
            result = result_ptr.decode('utf-8') if isinstance(result_ptr, bytes) else str(result_ptr)
            
            # Free the string pointer
            self._free_string(result_ptr)
            
            logger.debug("CreateBridge.create_pipeline: native call returned", {
                "bytes": len(result) if result else 0
            })
            
            return result
            
        except Exception as e:
            logger.error("CreateBridge.create_pipeline: error calling native function", {
                "basePath": base_path,
                "jsonFile": json_file,
                "deviceId": device_id,
                "error": str(e)
            })
            raise FfiBridgeError(f"Failed to create pipeline: {e}")
