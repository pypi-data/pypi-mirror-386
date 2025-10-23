"""
Base bridge implementation for Executor operations.

This module provides the base bridge class for communicating with the native
executor bridge library using FFI.
"""

import ctypes
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import ResponseStatus
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


class BaseExecutorBridge:
    """Base bridge class for executor operations."""
    
    def __init__(self, library_path: str, library_key: str = "executor_bridge"):
        """
        Initialize the base bridge.
        
        Args:
            library_path: Path to the executor bridge library
            library_key: Key for the library (for logging)
        """
        self.library_path = library_path
        self.library_key = library_key
        self._library = None
        self._is_initialized = False
    
    async def open(self) -> None:
        """Open the bridge library."""
        if self._is_initialized:
            return
        
        try:
            logger.debug(f"BaseExecutorBridge.open: opening library", {
                "libraryPath": self.library_path,
                "libraryKey": self.library_key
            })
            
            # Load the dynamic library
            self._library = ctypes.CDLL(self.library_path)
            
            # Set up function signatures
            self._setup_function_signatures()
            
            logger.info(f"BaseExecutorBridge.open: library opened successfully")
            self._is_initialized = True
            
        except Exception as e:
            logger.error(f"BaseExecutorBridge.open: failed to open library", {
                "libraryPath": self.library_path,
                "error": str(e)
            })
            raise FfiBridgeError(f"Failed to open executor bridge library: {e}")
    
    async def close(self) -> None:
        """Close the bridge library."""
        if not self._is_initialized:
            return
        
        try:
            logger.debug(f"BaseExecutorBridge.close: closing library", {
                "libraryKey": self.library_key
            })
            
            # Clean up resources
            self._library = None
            self._is_initialized = False
            
            logger.info(f"BaseExecutorBridge.close: library closed successfully")
            
        except Exception as e:
            logger.error(f"BaseExecutorBridge.close: failed to close library", {
                "libraryKey": self.library_key,
                "error": str(e)
            })
            # Don't raise here as we're cleaning up
    
    def _setup_function_signatures(self) -> None:
        """Set up function signatures for the bridge library."""
        if not self._library:
            return
        
        # Define function signatures for all executor bridge functions
        # These will be overridden by specific bridge implementations
        pass
    
    def _call_native_function(self, func_name: str, *args) -> str:
        """
        Call a native function and return the result.
        
        Args:
            func_name: Name of the function to call
            *args: Arguments to pass to the function
            
        Returns:
            JSON response string from the native function
        """
        if not self._is_initialized or not self._library:
            raise FfiBridgeError("Bridge not initialized")
        
        try:
            # Get the function from the library
            func = getattr(self._library, func_name, None)
            if not func:
                raise FfiBridgeError(f"Function {func_name} not found in library")
            
            # Call the function
            result = func(*args)
            
            # Convert result to string if needed
            if isinstance(result, bytes):
                return result.decode('utf-8')
            elif isinstance(result, str):
                return result
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"BaseExecutorBridge._call_native_function: error calling {func_name}", {
                "funcName": func_name,
                "error": str(e)
            })
            raise FfiBridgeError(f"Failed to call native function {func_name}: {e}")
    
    def _free_string(self, string_ptr) -> None:
        """
        Free a string pointer returned by the native library.
        
        Args:
            string_ptr: Pointer to the string to free
        """
        if not self._is_initialized or not self._library:
            return
        
        try:
            # Get the string_free function
            string_free = getattr(self._library, 'executor_bridge_string_free', None)
            if string_free:
                string_free(string_ptr)
        except Exception as e:
            logger.warning(f"BaseExecutorBridge._free_string: failed to free string", {
                "error": str(e)
            })
            # Don't raise here as this is cleanup
