"""
Install operator bridge functions.

This module provides the FFI bridge functions for installing operators,
following the same structure as the Node.js SDK.
"""

import logging
from typing import Optional
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ...dto.options import OperatorInstallOptions
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def install_operator(
    ffi: FFI,
    lib: any,
    base_path: str,
    name: str,
    version: str,
    options: OperatorInstallOptions
) -> str:
    """
    Install an operator.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        name: Operator name
        version: Operator version
        options: Installation options
        
    Returns:
        JSON string containing installation result
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Installing operator: {name}@{version}, platform={options.platform}, force={options.force}")
        
        # Convert Python parameters to C parameters
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        c_name = ffi.new("char[]", name.encode('utf-8'))
        c_version = ffi.new("char[]", version.encode('utf-8'))
        c_platform = ffi.NULL
        if options.platform:
            c_platform = ffi.new("char[]", options.platform.encode('utf-8'))
        c_force = 1 if options.force else 0
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_install(
            c_base_path,
            c_name,
            c_version,
            c_platform,
            c_force
        )
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "Install operator operation returned NULL",
                function_name="operator_registry_bridge_install",
                parameters={
                    "base_path": base_path,
                    "name": name,
                    "version": version,
                    "platform": options.platform,
                    "force": options.force
                }
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"Install operator operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"Install operator operation failed: {e}")
        raise FfiBridgeError(
            f"Install operator operation failed: {e}",
            function_name="operator_registry_bridge_install",
            parameters={
                "base_path": base_path,
                "name": name,
                "version": version,
                "platform": options.platform,
                "force": options.force
            }
        )
