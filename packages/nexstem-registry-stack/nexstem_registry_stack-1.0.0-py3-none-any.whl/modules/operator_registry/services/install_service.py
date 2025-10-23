"""
Install operator service implementation.

This module provides the service function for installing operators,
following the same structure as the Node.js SDK.
"""

import json
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.operator_registry_bridge import OperatorRegistryBridge
from ..dto.options import OperatorInstallOptions
from ..dto.responses import OperatorInstallResponse
from shared.dto.common import ResponseStatus, ErrorDetails

logger = logging.getLogger(__name__)


async def install_operator(
    base_path: str,
    bridge: OperatorRegistryBridge,
    name: str,
    version: str,
    options: OperatorInstallOptions
) -> OperatorInstallResponse:
    """
    Install operator service function.
    
    Args:
        base_path: Base path for operations
        bridge: Operator registry bridge instance
        name: Operator name
        version: Operator version
        options: Install options
        
    Returns:
        Operator install response
    """
    try:
        logger.debug(f"Installing operator: {name}@{version}, force={options.force}")
        
        # Use the bridge to install operator
        json_response = bridge.install_operator(base_path, name, version, options)
        
        # Parse the JSON response
        response_data = json.loads(json_response)
        
        # Convert to our response type
        if response_data.get("status") == "success":
            from ..dto.responses import OperatorInstallData
            data = OperatorInstallData(**response_data["data"])
            return OperatorInstallResponse(
                status=ResponseStatus.SUCCESS,
                message=response_data.get("message", "Operator installed successfully"),
                data=data
            )
        else:
            return OperatorInstallResponse(
                status=ResponseStatus.ERROR,
                message=response_data.get("message", "Failed to install operator"),
                data=None,
                error=ErrorDetails(
                    message=response_data.get("message", "Unknown error"),
                    type="bridge_error"
                )
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return OperatorInstallResponse(
            status=ResponseStatus.ERROR,
            message="Failed to parse response from operator registry",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="json_parse_error"
            )
        )
    except Exception as e:
        logger.error(f"Install operation failed: {e}")
        return OperatorInstallResponse(
            status=ResponseStatus.ERROR,
            message="Failed to install operator",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="bridge_error"
            )
        )
