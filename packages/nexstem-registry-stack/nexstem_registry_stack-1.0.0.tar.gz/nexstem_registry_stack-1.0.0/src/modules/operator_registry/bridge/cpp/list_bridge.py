"""
List operators bridge functions.

This module provides the FFI bridge functions for listing operators,
following the same structure as the Node.js SDK.
"""

import logging
from typing import Optional
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ...dto.options import OperatorListOptions
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def list_operators(
    ffi: FFI,
    lib: any,
    base_path: str
) -> str:
    """
    List local operators.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        
    Returns:
        JSON string containing operator list
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Listing operators at base path: {base_path}")
        
        # Convert Python string to C string
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_list(c_base_path)
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "List operation returned NULL",
                function_name="operator_registry_bridge_list",
                parameters={"base_path": base_path}
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"List operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"List operation failed: {e}")
        raise FfiBridgeError(
            f"List operation failed: {e}",
            function_name="operator_registry_bridge_list",
            parameters={"base_path": base_path}
        )


def list_operators_with_options(
    ffi: FFI,
    lib: any,
    base_path: str,
    options: OperatorListOptions
) -> str:
    """
    List operators with options.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        options: List options
        
    Returns:
        JSON string containing operator list
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Listing operators with options: {options.dict()}")
        
        # Convert Python parameters to C parameters
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        c_remote = 1 if options.remote else 0
        c_page = options.page or 1
        c_page_size = options.page_size or 25
        c_operator_name = ffi.NULL
        if options.operator:
            c_operator_name = ffi.new("char[]", options.operator.encode('utf-8'))
        c_versions = 1 if options.versions else 0
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_list_with_options(
            c_base_path,
            c_remote,
            c_page,
            c_page_size,
            c_operator_name,
            c_versions
        )
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "List with options operation returned NULL",
                function_name="operator_registry_bridge_list_with_options",
                parameters={
                    "base_path": base_path,
                    "options": options.dict()
                }
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"List with options operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"List with options operation failed: {e}")
        raise FfiBridgeError(
            f"List with options operation failed: {e}",
            function_name="operator_registry_bridge_list_with_options",
            parameters={
                "base_path": base_path,
                "options": options.dict()
            }
        )
