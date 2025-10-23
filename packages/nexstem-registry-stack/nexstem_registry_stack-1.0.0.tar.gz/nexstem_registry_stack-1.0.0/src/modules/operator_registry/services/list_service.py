"""
List operators service implementation.

This module provides the service function for listing operators,
following the same structure as the Node.js SDK.
"""

import json
import logging
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.operator_registry_bridge import OperatorRegistryBridge
from ..dto.options import OperatorListOptions
from ..dto.responses import OperatorListResponse, OperatorListData
from shared.dto.common import ResponseStatus, ErrorDetails

logger = logging.getLogger(__name__)


async def list_operators(
    base_path: str,
    bridge: OperatorRegistryBridge,
    options: Optional[OperatorListOptions] = None
) -> OperatorListResponse:
    """
    List operators service function.
    
    Args:
        base_path: Base path for operations
        bridge: Operator registry bridge instance
        options: List options
        
    Returns:
        Operator list response
    """
    if options is None:
        options = OperatorListOptions()
    
    try:
        logger.debug(f"Listing operators with options: {options.dict()}")
        
        # Use the bridge to get the JSON response
        if options.remote or options.operator or options.versions or options.page or options.page_size:
            # Use the full options function
            json_response = bridge.list_operators_with_options(base_path, options)
        else:
            # Use the simple list function
            json_response = bridge.list_operators(base_path)
        
        # Parse the JSON response
        response_data = json.loads(json_response)
        
        # Convert to our response type
        if response_data.get("status") == "success":
            # Handle different response formats
            data_dict = response_data["data"]
            
            # Handle different response formats to match Node.js exactly
            operators = data_dict.get("operators", [])
            versions = data_dict.get("versions", [])
            
            # For local operations, ensure operators are objects
            if not options.remote and operators and isinstance(operators[0], str):
                # Convert string names to Operator objects for local operations
                operator_objects = []
                for name in operators:
                    operator_objects.append({
                        "name": name,
                        "version": "unknown",
                        "platform": "unknown", 
                        "install_path": "",
                        "description": "",
                        "metadata": None
                    })
                data_dict["operators"] = operator_objects
            
            # For remote operations, keep the original format:
            # - operators as strings for remote list
            # - versions as strings for remote versions
            # - operators as objects for remote filtered (if needed)
            
            data = OperatorListData(**data_dict)
            return OperatorListResponse(
                status=ResponseStatus.SUCCESS,
                message=response_data.get("message", "Operators listed successfully"),
                data=data
            )
        else:
            return OperatorListResponse(
                status=ResponseStatus.ERROR,
                message=response_data.get("message", "Failed to list operators"),
                data=OperatorListData(count=0, operators=[]),
                error=ErrorDetails(
                    message=response_data.get("message", "Unknown error"),
                    type="bridge_error"
                )
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return OperatorListResponse(
            status=ResponseStatus.ERROR,
            message="Failed to parse response from operator registry",
            data=OperatorListData(count=0, operators=[]),
            error=ErrorDetails(
                message=str(e),
                type="json_parse_error"
            )
        )
    except Exception as e:
        logger.error(f"List operation failed: {e}")
        return OperatorListResponse(
            status=ResponseStatus.ERROR,
            message="Failed to list operators",
            data=OperatorListData(count=0, operators=[]),
            error=ErrorDetails(
                message=str(e),
                type="bridge_error"
            )
        )
