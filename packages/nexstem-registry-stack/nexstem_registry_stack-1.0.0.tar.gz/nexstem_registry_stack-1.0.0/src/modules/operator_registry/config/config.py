"""
Operator Registry configuration implementation.

This module provides the configuration class for the Operator Registry service,
following the same structure as the Node.js SDK.
"""

import os
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import BaseConfig


class OperatorRegistryConfiguration(BaseConfig):
    """Configuration class for Operator Registry."""
    
    def __init__(
        self,
        base_path: Optional[str] = None,
        bridge_lib_path: Optional[str] = None,
        timeout: Optional[int] = None,
        debug: Optional[bool] = None,
        pretty: Optional[bool] = None,
    ) -> None:
        """
        Initialize operator registry configuration.
        
        Args:
            base_path: Base path for local operations
            bridge_lib_path: Path to the native bridge library
            timeout: Request timeout in milliseconds
            debug: Enable debug mode
            pretty: Pretty print JSON output
        """
        # Set defaults from environment variables
        super().__init__(
            base_path=base_path or os.getenv("SW_REGISTRY_BASE_PATH", "/opt/operators"),
            bridge_lib_path=bridge_lib_path or os.getenv(
                "SW_REGISTRY_BRIDGE_LIB_PATH",
                "/usr/local/lib/registry-stack/liboperator_registry_bridge.dylib"
            ),
            timeout=timeout or int(os.getenv("SW_REGISTRY_TIMEOUT", "30000")),
            debug=debug if debug is not None else os.getenv("SW_REGISTRY_DEBUG", "false").lower() == "true",
            pretty=pretty if pretty is not None else os.getenv("SW_REGISTRY_PRETTY", "false").lower() == "true",
        )
