"""
Operator Registry FFI bridge implementation.

This module provides the main FFI bridge class for communicating with the native
operator registry library using CFFI, following the same structure as the Node.js SDK.
"""

import logging
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.bridge.base_bridge import BaseBridge
from ..dto.options import (
    OperatorListOptions,
    OperatorInstallOptions,
    OperatorUninstallOptions,
    OperatorInfoOptions,
    OperatorPushOptions,
)
from .cpp.list_bridge import list_operators, list_operators_with_options
from .cpp.info_bridge import get_operator_info
from .cpp.install_bridge import install_operator
from .cpp.uninstall_bridge import uninstall_operator
from .cpp.push_bridge import push_operator
from .cpp.free_bridge import free_string

logger = logging.getLogger(__name__)


class OperatorRegistryBridge(BaseBridge):
    """
    FFI bridge for Operator Registry operations.
    
    This class provides the interface for calling native operator registry
    functions through CFFI, including operator listing, installation,
    uninstallation, and information retrieval.
    """
    
    def __init__(self, library_path: str) -> None:
        """
        Initialize the operator registry bridge.
        
        Args:
            library_path: Path to the liboperator_registry_bridge library
        """
        super().__init__(
            library_path=library_path,
            library_key="operator_registry_bridge"
        )
    
    def _define_functions(self) -> None:
        """Define function signatures for the operator registry bridge."""
        self._ffi.cdef("""
            // Return JSON (UTF-8) for local list of operators at base_path.
            // The returned pointer is a newly allocated buffer and must be freed with
            // operator_registry_bridge_string_free.
            const char* operator_registry_bridge_list(const char* base_path);
            
            // Return JSON (UTF-8) for list of operators with full options:
            // - base_path: base path for local operations
            // - remote: 1 for remote, 0 for local
            // - page: page number (1-based)
            // - page_size: number of items per page
            // - operator_name: filter by operator name (NULL for no filter)
            // - versions: 1 for versions listing, 0 for normal listing
            const char* operator_registry_bridge_list_with_options(
                const char* base_path, 
                int remote, 
                int page, 
                int page_size, 
                const char* operator_name, 
                int versions
            );
            
            // Return JSON (UTF-8) for operator info.
            // - remote: 1 for remote, 0 for local
            // - name: operator name
            // - version: operator version
            const char* operator_registry_bridge_info(
                const char* base_path,
                int remote,
                const char* name,
                const char* version
            );
            
            // Install an operator. Returns JSON (UTF-8).
            // - name: operator name
            // - version: operator version
            // - platform: target platform (e.g., "linux_arm64"). If NULL, auto-detect
            // - force: 1 to force re-download/reinstall, 0 otherwise
            const char* operator_registry_bridge_install(
                const char* base_path,
                const char* name,
                const char* version,
                const char* platform,
                int force
            );
            
            // Push an operator tar.gz to remote registry and optionally register locally. Returns JSON (UTF-8).
            // - name: operator name
            // - version: operator version
            // - tar_path: path to the .tar.gz
            // - local_only: 1 to skip remote push and only register locally, 0 to push then register
            const char* operator_registry_bridge_push(
                const char* base_path,
                const char* name,
                const char* version,
                const char* tar_path,
                int local_only
            );
            
            // Uninstall an operator. Returns JSON (UTF-8).
            // - name: operator name
            // - version: operator version
            const char* operator_registry_bridge_uninstall(
                const char* base_path,
                const char* name,
                const char* version
            );
            
            // Free a C string returned by bridge functions
            void operator_registry_bridge_string_free(const char* s);
        """)
    
    def list_operators(self, base_path: str) -> str:
        """
        List local operators.
        
        Args:
            base_path: Base path for local operations
            
        Returns:
            JSON string containing operator list
        """
        return list_operators(self._ffi, self._lib, base_path)
    
    def list_operators_with_options(
        self,
        base_path: str,
        options: OperatorListOptions
    ) -> str:
        """
        List operators with options.
        
        Args:
            base_path: Base path for local operations
            options: List options
            
        Returns:
            JSON string containing operator list
        """
        return list_operators_with_options(self._ffi, self._lib, base_path, options)
    
    def get_operator_info(
        self,
        base_path: str,
        name: str,
        version: str,
        options: OperatorInfoOptions
    ) -> str:
        """
        Get operator information.
        
        Args:
            base_path: Base path for local operations
            name: Operator name
            version: Operator version
            options: Info options
            
        Returns:
            JSON string containing operator information
        """
        return get_operator_info(self._ffi, self._lib, base_path, name, version, options)
    
    def install_operator(
        self,
        base_path: str,
        name: str,
        version: str,
        options: OperatorInstallOptions
    ) -> str:
        """
        Install an operator.
        
        Args:
            base_path: Base path for local operations
            name: Operator name
            version: Operator version
            options: Installation options
            
        Returns:
            JSON string containing installation result
        """
        return install_operator(self._ffi, self._lib, base_path, name, version, options)
    
    def uninstall_operator(
        self,
        base_path: str,
        name: str,
        version: str,
        options: OperatorUninstallOptions
    ) -> str:
        """
        Uninstall an operator.
        
        Args:
            base_path: Base path for local operations
            name: Operator name
            version: Operator version
            options: Uninstall options
            
        Returns:
            JSON string containing uninstallation result
        """
        return uninstall_operator(self._ffi, self._lib, base_path, name, version, options)
    
    def push_operator(
        self,
        base_path: str,
        name: str,
        version: str,
        tar_path: str,
        options: OperatorPushOptions
    ) -> str:
        """
        Push an operator to the registry.
        
        Args:
            base_path: Base path for local operations
            name: Operator name
            version: Operator version
            tar_path: Path to the operator tar.gz file
            options: Push options
            
        Returns:
            JSON string containing push result
        """
        return push_operator(self._ffi, self._lib, base_path, name, version, tar_path, options)
    
    def free_string(self, str_ptr: any) -> None:
        """
        Free a C string returned by bridge functions.
        
        Args:
            str_ptr: Pointer to the C string to free
        """
        free_string(self._ffi, self._lib, str_ptr)
