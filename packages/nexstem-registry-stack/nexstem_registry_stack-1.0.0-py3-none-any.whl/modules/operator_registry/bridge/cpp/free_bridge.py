"""
Free string bridge functions.

This module provides the FFI bridge functions for freeing strings,
following the same structure as the Node.js SDK.
"""

import logging
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def free_string(
    ffi: FFI,
    lib: any,
    str_ptr: any
) -> None:
    """
    Free a C string returned by bridge functions.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        str_ptr: Pointer to the C string to free
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Freeing string pointer: {str_ptr}")
        
        # Call native function
        lib.operator_registry_bridge_string_free(str_ptr)
        
        logger.debug("String freed successfully")
        
    except Exception as e:
        logger.error(f"Free string operation failed: {e}")
        raise FfiBridgeError(
            f"Free string operation failed: {e}",
            function_name="operator_registry_bridge_string_free",
            parameters={"str_ptr": str(str_ptr)}
        )
