"""
Base bridge class for FFI integration.

This module provides the base functionality for all FFI bridges,
including library loading, error handling, and common operations.
"""

import os
import logging
from typing import Any, Dict, Optional
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from exceptions import FfiBridgeError, ConfigurationError

logger = logging.getLogger(__name__)


class BaseBridge:
    """
    Base class for all FFI bridges.
    
    This class provides common functionality for loading native libraries,
    managing FFI instances, and handling errors consistently across all bridges.
    """
    
    def __init__(
        self,
        library_path: str,
        library_key: str,
    ) -> None:
        """
        Initialize the base bridge.
        
        Args:
            library_path: Path to the native library file
            library_key: Unique key for the library instance
            
        Raises:
            ConfigurationError: If library path is invalid
        """
        self.library_path = library_path
        self.library_key = library_key
        self._ffi = None
        self._lib = None
        self._is_loaded = False
        
        # Validate library path
        if not library_path or not os.path.exists(library_path):
            raise ConfigurationError(
                f"Library not found: {library_path}",
                config_key="library_path",
                config_value=library_path
            )
        
        logger.debug(f"Initialized bridge {library_key} with library: {library_path}")
    
    def load(self) -> None:
        """
        Load the native library and initialize FFI.
        
        Raises:
            FfiBridgeError: If library loading fails
        """
        if self._is_loaded:
            logger.debug(f"Library {self.library_key} already loaded")
            return
        
        try:
            logger.debug(f"Loading library {self.library_key} from {self.library_path}")
            
            # Initialize FFI
            self._ffi = FFI()
            
            # Define function signatures
            self._define_functions()
            
            # Load the library
            self._lib = self._ffi.dlopen(self.library_path)
            
            self._is_loaded = True
            logger.info(f"Successfully loaded library {self.library_key}")
            
        except Exception as e:
            logger.error(f"Failed to load library {self.library_key}: {e}")
            raise FfiBridgeError(
                f"Failed to load library {self.library_key}: {e}",
                function_name="load",
                parameters={"library_path": self.library_path}
            )
    
    def unload(self) -> None:
        """
        Unload the native library and cleanup resources.
        """
        if not self._is_loaded:
            logger.debug(f"Library {self.library_key} not loaded, skipping unload")
            return
        
        try:
            logger.debug(f"Unloading library {self.library_key}")
            
            # Cleanup FFI resources
            self._lib = None
            self._ffi = None
            self._is_loaded = False
            
            logger.info(f"Successfully unloaded library {self.library_key}")
            
        except Exception as e:
            logger.warning(f"Error during library unload {self.library_key}: {e}")
    
    @property
    def lib(self):
        """
        Access to the loaded library.
        
        Returns:
            The loaded library object
            
        Raises:
            FfiBridgeError: If library is not loaded
        """
        if not self._is_loaded or self._lib is None:
            raise FfiBridgeError(
                f"Library {self.library_key} is not loaded",
                function_name="lib",
                parameters={"library_key": self.library_key}
            )
        return self._lib
    
    def is_loaded(self) -> bool:
        """
        Check if the library is currently loaded.
        
        Returns:
            True if the library is loaded, False otherwise
        """
        return self._is_loaded
    
    def ensure_loaded(self) -> None:
        """
        Ensure the library is loaded, loading it if necessary.
        
        Raises:
            FfiBridgeError: If library loading fails
        """
        if not self._is_loaded:
            self.load()
    
    def _define_functions(self) -> None:
        """
        Define function signatures for FFI.
        
        This method should be overridden by subclasses to define
        the specific function signatures for their native library.
        """
        raise NotImplementedError("Subclasses must implement _define_functions")
    
    def __enter__(self) -> "BaseBridge":
        """Context manager entry."""
        self.load()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.unload()
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        try:
            self.unload()
        except Exception:
            # Ignore errors during cleanup
            pass
