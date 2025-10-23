"""
Operator Registry service implementation.

This module provides the main OperatorRegistry class for managing operators
in the SW Registry Stack, following the same structure as the Node.js SDK.
"""

import logging
from typing import Optional, Union
from .bridge.operator_registry_bridge import OperatorRegistryBridge
from .config.config import OperatorRegistryConfiguration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .dto.options import (
    OperatorListOptions,
    OperatorInstallOptions,
    OperatorUninstallOptions,
    OperatorInfoOptions,
    OperatorStatusOptions,
    OperatorPushOptions,
    OperatorRepairOptions,
)
from .dto.responses import (
    OperatorListResponse,
    OperatorInstallResponse,
    OperatorUninstallResponse,
    OperatorInfoResponse,
    OperatorStatusResponse,
    OperatorPushResponse,
    OperatorRepairResponse,
)
from exceptions import (
    SdkError,
    ValidationError,
    FfiBridgeError,
    ConfigurationError,
)
from shared.dto.common import ResponseStatus, ErrorDetails
from .services.list_service import list_operators
from .services.info_service import get_operator_info
from .services.install_service import install_operator
from .services.uninstall_service import uninstall_operator

logger = logging.getLogger(__name__)


class OperatorRegistry:
    """
    Main Operator Registry service class.
    
    This class provides the primary interface for managing operators in the
    SW Registry Stack, following the same structure as the Node.js SDK.
    """
    
    def __init__(self, config: Optional[Union[OperatorRegistryConfiguration, dict]] = None) -> None:
        """
        Initialize the Operator Registry service.
        
        Args:
            config: Configuration object or dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if isinstance(config, dict):
            self.config = OperatorRegistryConfiguration(**config)
        elif config is None:
            self.config = OperatorRegistryConfiguration()
        else:
            self.config = config
        
        # Initialize bridge
        try:
            self.bridge = OperatorRegistryBridge(self.config.bridge_lib_path)
            self._is_initialized = False
            
            logger.debug(f"Initialized OperatorRegistry with base_path: {self.config.base_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OperatorRegistry: {e}")
            raise ConfigurationError(
                f"Failed to initialize OperatorRegistry: {e}",
                config_key="bridge_lib_path",
                config_value=self.config.bridge_lib_path
            )
    
    async def initialize(self) -> None:
        """
        Initialize the operator registry service.
        
        Raises:
            FfiBridgeError: If initialization fails
        """
        if self._is_initialized:
            logger.debug("OperatorRegistry already initialized")
            return
        
        try:
            logger.debug("Initializing OperatorRegistry service")
            self.bridge.load()
            self._is_initialized = True
            logger.info("OperatorRegistry service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OperatorRegistry service: {e}")
            raise FfiBridgeError(
                f"Failed to initialize OperatorRegistry service: {e}",
                function_name="initialize",
                parameters={"config": self.config.dict()}
            )
    
    async def close(self) -> None:
        """
        Close the operator registry service and cleanup resources.
        """
        if not self._is_initialized:
            logger.debug("OperatorRegistry not initialized, skipping close")
            return
        
        try:
            logger.debug("Closing OperatorRegistry service")
            self.bridge.unload()
            self._is_initialized = False
            logger.info("OperatorRegistry service closed successfully")
            
        except Exception as e:
            logger.warning(f"Error during OperatorRegistry cleanup: {e}")
    
    def _ensure_initialized(self) -> None:
        """
        Ensure the service is initialized before operations.
        
        Raises:
            SdkError: If the service is not initialized
        """
        if not self._is_initialized:
            raise SdkError(
                "OperatorRegistry service is not initialized. Call initialize() first.",
                error_type="not_initialized"
            )
    
    def _validate_name_version(self, name_version: str) -> None:
        """
        Validate name@version format.
        
        Args:
            name_version: Name@version string to validate
            
        Raises:
            ValidationError: If format is invalid
        """
        if not name_version or "@" not in name_version:
            raise ValidationError(
                "Invalid name@version format",
                field="name_version",
                value=name_version
            )
        
        parts = name_version.split("@")
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise ValidationError(
                "Invalid name@version format",
                field="name_version",
                value=name_version
            )
    
    def _parse_name_version(self, name_version: str) -> tuple[str, str]:
        """
        Parse name@version string into name and version.
        
        Args:
            name_version: Name@version string
            
        Returns:
            Tuple of (name, version)
        """
        self._validate_name_version(name_version)
        return name_version.split("@")
    
    async def list(self, options: Optional[OperatorListOptions] = None) -> OperatorListResponse:
        """
        List operators (installed or remote).
        
        Args:
            options: List options including pagination and filtering
            
        Returns:
            List of operators
        """
        self._ensure_initialized()
        return await list_operators(self.config.base_path, self.bridge, options)
    
    async def install(
        self,
        name: str,
        version: str,
        options: Optional[OperatorInstallOptions] = None
    ) -> OperatorInstallResponse:
        """
        Install an operator.
        
        Args:
            name: Operator name
            version: Operator version
            options: Installation options
            
        Returns:
            Installation result
            
        Raises:
            ValidationError: If name or version are invalid
            FfiBridgeError: If the operation fails
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorInstallOptions()
        
        if not name or not version:
            raise ValidationError(
                "Name and version are required",
                field="name,version",
                value={"name": name, "version": version}
            )
        
        return await install_operator(self.config.base_path, self.bridge, name, version, options)
    
    async def uninstall(
        self,
        name: str,
        version: str,
        options: Optional[OperatorUninstallOptions] = None
    ) -> OperatorUninstallResponse:
        """
        Uninstall an operator.
        
        Args:
            name: Operator name
            version: Operator version
            options: Uninstall options
            
        Returns:
            Uninstallation result
            
        Raises:
            ValidationError: If name or version are invalid
            FfiBridgeError: If the operation fails
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorUninstallOptions()
        
        if not name or not version:
            raise ValidationError(
                "Name and version are required",
                field="name,version",
                value={"name": name, "version": version}
            )
        
        return await uninstall_operator(self.config.base_path, self.bridge, name, version, options)
    
    async def info(
        self,
        name: str,
        version: str,
        options: Optional[OperatorInfoOptions] = None
    ) -> OperatorInfoResponse:
        """
        Get operator information.
        
        Args:
            name: Operator name
            version: Operator version
            options: Info options
            
        Returns:
            Operator information
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorInfoOptions()
        
        return await get_operator_info(self.config.base_path, self.bridge, name, version, options)
    
    async def status(
        self,
        name_version: str,
        options: Optional[OperatorStatusOptions] = None
    ) -> OperatorStatusResponse:
        """
        Get operator installation status.
        
        Args:
            name_version: Operator name@version
            options: Status options
            
        Returns:
            Installation status
            
        Raises:
            ValidationError: If name_version is invalid
            SdkError: If the operation is not implemented
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorStatusOptions()
        
        # Parse name and version
        name, version = self._parse_name_version(name_version)
        
        # This operation is not yet implemented in the bridge
        raise SdkError(
            "Status operation not yet implemented - bridge only supports listing",
            error_type="not_implemented"
        )
    
    async def push(
        self,
        name_version: str,
        tar_path: str,
        options: Optional[OperatorPushOptions] = None
    ) -> OperatorPushResponse:
        """
        Push an operator to the remote registry.
        
        Args:
            name_version: Operator name@version
            tar_path: Path to the operator tar.gz file
            options: Push options
            
        Returns:
            Push result
            
        Raises:
            ValidationError: If parameters are invalid
            FfiBridgeError: If the operation fails
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorPushOptions()
        
        # Parse name and version
        name, version = self._parse_name_version(name_version)
        
        # This would use a push service function when implemented
        raise SdkError(
            "Push operation not yet implemented in services layer",
            error_type="not_implemented"
        )
    
    async def repair(
        self,
        options: Optional[OperatorRepairOptions] = None
    ) -> OperatorRepairResponse:
        """
        Repair the local operator registry.
        
        Args:
            options: Repair options
            
        Returns:
            Repair result
            
        Raises:
            SdkError: If the operation is not implemented
        """
        self._ensure_initialized()
        
        if options is None:
            options = OperatorRepairOptions()
        
        # This operation is not yet implemented in the bridge
        raise SdkError(
            "Repair operation not yet implemented - bridge only supports listing",
            error_type="not_implemented"
        )
    
    def get_config(self) -> OperatorRegistryConfiguration:
        """
        Get the current configuration.
        
        Returns:
            Current configuration object
        """
        return self.config
    
    def is_initialized(self) -> bool:
        """
        Check if the service is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._is_initialized
    
    async def __aenter__(self) -> "OperatorRegistry":
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        """Async context manager exit."""
        await self.close()
