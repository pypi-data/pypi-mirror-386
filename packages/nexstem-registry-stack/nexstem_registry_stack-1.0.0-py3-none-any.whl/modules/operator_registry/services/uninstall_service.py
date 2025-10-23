"""
Uninstall service for Operator Registry.

This module provides the uninstall_operator function for removing operators
from the local registry, following the same structure as other services.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.operator_registry_bridge import OperatorRegistryBridge
from ..dto.options import OperatorUninstallOptions
from ..dto.responses import OperatorUninstallResponse, OperatorUninstallData
from shared.dto.common import ResponseStatus, ErrorDetails

logger = logging.getLogger(__name__)


async def uninstall_operator(
    base_path: str,
    bridge: OperatorRegistryBridge,
    name: str,
    version: str,
    options: Optional[OperatorUninstallOptions] = None
) -> OperatorUninstallResponse:
    """
    Uninstall an operator from the local registry.
    
    Args:
        base_path: Base path for the registry
        bridge: Bridge instance for native calls
        name: Operator name
        version: Operator version
        options: Uninstall options
        
    Returns:
        Uninstall response with result
    """
    try:
        logger.debug(f"Uninstalling operator: {name}@{version}")
        
        # Use the bridge to uninstall operator
        json_response = bridge.uninstall_operator(base_path, name, version, options)
        
        # Parse the JSON response
        response_data = json.loads(json_response)
        
        # Convert to our response type
        if response_data.get("status") == "success":
            from ..dto.responses import OperatorUninstallData
            data = OperatorUninstallData(**response_data["data"]) if response_data.get("data") else None
            return OperatorUninstallResponse(
                status=ResponseStatus.SUCCESS,
                message=response_data.get("message", "Operator uninstalled successfully"),
                data=data
            )
        else:
            return OperatorUninstallResponse(
                status=ResponseStatus.ERROR,
                message=response_data.get("message", "Failed to uninstall operator"),
                data=None,
                error=ErrorDetails(
                    message=response_data.get("message", "Unknown error"),
                    type="bridge_error"
                )
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return OperatorUninstallResponse(
            status=ResponseStatus.ERROR,
            message="Failed to parse response from operator registry",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="json_parse_error"
            )
        )
    except Exception as e:
        logger.error(f"Uninstall operation failed: {e}")
        return OperatorUninstallResponse(
            status=ResponseStatus.ERROR,
            message="Failed to uninstall operator",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="bridge_error"
            )
        )
