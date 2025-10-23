"""
Get operator info bridge functions.

This module provides the FFI bridge functions for getting operator information,
following the same structure as the Node.js SDK.
"""

import logging
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ...dto.options import OperatorInfoOptions
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def get_operator_info(
    ffi: FFI,
    lib: any,
    base_path: str,
    name: str,
    version: str,
    options: OperatorInfoOptions
) -> str:
    """
    Get operator information.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        name: Operator name
        version: Operator version
        options: Info options
        
    Returns:
        JSON string containing operator information
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Getting operator info: {name}@{version}, remote={options.remote}")
        
        # Convert Python parameters to C parameters
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        c_remote = 1 if options.remote else 0
        c_name = ffi.new("char[]", name.encode('utf-8'))
        c_version = ffi.new("char[]", version.encode('utf-8'))
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_info(
            c_base_path,
            c_remote,
            c_name,
            c_version
        )
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "Get operator info operation returned NULL",
                function_name="operator_registry_bridge_info",
                parameters={
                    "base_path": base_path,
                    "remote": options.remote,
                    "name": name,
                    "version": version
                }
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"Get operator info operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"Get operator info operation failed: {e}")
        raise FfiBridgeError(
            f"Get operator info operation failed: {e}",
            function_name="operator_registry_bridge_info",
            parameters={
                "base_path": base_path,
                "remote": options.remote,
                "name": name,
                "version": version
            }
        )
