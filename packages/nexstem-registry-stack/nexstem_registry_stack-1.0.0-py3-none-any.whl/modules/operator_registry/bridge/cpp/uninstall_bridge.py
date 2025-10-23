"""
Uninstall operator bridge functions.

This module provides the FFI bridge functions for uninstalling operators,
following the same structure as the Node.js SDK.
"""

import logging
from cffi import FFI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from ...dto.options import OperatorUninstallOptions
from exceptions import FfiBridgeError

logger = logging.getLogger(__name__)


def uninstall_operator(
    ffi: FFI,
    lib: any,
    base_path: str,
    name: str,
    version: str,
    options: OperatorUninstallOptions
) -> str:
    """
    Uninstall an operator.
    
    Args:
        ffi: CFFI instance
        lib: Loaded library instance
        base_path: Base path for local operations
        name: Operator name
        version: Operator version
        options: Uninstall options
        
    Returns:
        JSON string containing uninstallation result
        
    Raises:
        FfiBridgeError: If the operation fails
    """
    try:
        logger.debug(f"Uninstalling operator: {name}@{version}")
        
        # Convert Python parameters to C parameters
        c_base_path = ffi.new("char[]", base_path.encode('utf-8'))
        c_name = ffi.new("char[]", name.encode('utf-8'))
        c_version = ffi.new("char[]", version.encode('utf-8'))
        
        # Call native function
        result_ptr = lib.operator_registry_bridge_uninstall(
            c_base_path,
            c_name,
            c_version
        )
        
        if result_ptr == ffi.NULL:
            raise FfiBridgeError(
                "Uninstall operator operation returned NULL",
                function_name="operator_registry_bridge_uninstall",
                parameters={
                    "base_path": base_path,
                    "name": name,
                    "version": version
                }
            )
        
        # Convert C string to Python string
        result = ffi.string(result_ptr).decode('utf-8')
        
        # Free the C string
        lib.operator_registry_bridge_string_free(result_ptr)
        
        logger.debug(f"Uninstall operator operation completed, returned {len(result)} characters")
        return result
        
    except Exception as e:
        logger.error(f"Uninstall operator operation failed: {e}")
        raise FfiBridgeError(
            f"Uninstall operator operation failed: {e}",
            function_name="operator_registry_bridge_uninstall",
            parameters={
                "base_path": base_path,
                "name": name,
                "version": version
            }
        )
