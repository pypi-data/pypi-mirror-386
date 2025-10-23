"""
Push operator bridge functions.

This module provides the FFI bridge functions for pushing operators,
following the same structure as the Node.js SDK.
"""

import logging
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ...dto.options import OperatorPushOptions
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def push_operator(
    ffi: FFI,
    lib: any,
    base_path: str,
    name: str,
    version: str,
    tar_path: str,
    options: OperatorPushOptions
) -> str:
    """
    Push an operator to the registry.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        name: Operator name
        version: Operator version
        tar_path: Path to the operator tar.gz file
        options: Push options
        
    Returns:
        JSON string containing push result
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Pushing operator: {name}@{version}, tar_path={tar_path}, local_only={options.local}")
        
        # Convert Python parameters to C parameters
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        c_name = ffi.new("char[]", name.encode('utf-8'))
        c_version = ffi.new("char[]", version.encode('utf-8'))
        c_tar_path = ffi.new("char[]", tar_path.encode('utf-8'))
        c_local_only = 1 if options.local else 0
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_push(
            c_base_path,
            c_name,
            c_version,
            c_tar_path,
            c_local_only
        )
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "Push operator operation returned NULL",
                function_name="operator_registry_bridge_push",
                parameters={
                    "base_path": base_path,
                    "name": name,
                    "version": version,
                    "tar_path": tar_path,
                    "local_only": options.local
                }
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"Push operator operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"Push operator operation failed: {e}")
        raise FfiBridgeError(
            f"Push operator operation failed: {e}",
            function_name="operator_registry_bridge_push",
            parameters={
                "base_path": base_path,
                "name": name,
                "version": version,
                "tar_path": tar_path,
                "local_only": options.local
            }
        )
