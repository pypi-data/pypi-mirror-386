"""
Get operator info service implementation.

This module provides the service function for getting operator information,
following the same structure as the Node.js SDK.
"""

import json
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..bridge.operator_registry_bridge import OperatorRegistryBridge
from ..dto.options import OperatorInfoOptions
from ..dto.responses import OperatorInfoResponse
from ..dto.operator_info import OperatorInfo
from shared.dto.common import ResponseStatus, ErrorDetails

logger = logging.getLogger(__name__)


async def get_operator_info(
    base_path: str,
    bridge: OperatorRegistryBridge,
    name: str,
    version: str,
    options: OperatorInfoOptions
) -> OperatorInfoResponse:
    """
    Get operator info service function.
    
    Args:
        base_path: Base path for operations
        bridge: Operator registry bridge instance
        name: Operator name
        version: Operator version
        options: Info options
        
    Returns:
        Operator info response
    """
    try:
        logger.debug(f"Getting operator info: {name}@{version}, remote={options.remote}")
        
        # Use the bridge to get operator info
        json_response = bridge.get_operator_info(base_path, name, version, options)
        
        # Parse the JSON response
        response_data = json.loads(json_response)
        
        # Convert to our response type
        if response_data.get("status") == "success":
            data_dict = response_data.get("data")
            if data_dict is None:
                # Handle case where data is null (e.g., operator not found)
                return OperatorInfoResponse(
                    status=ResponseStatus.ERROR,
                    message=response_data.get("message", "Operator not found"),
                    data=None,
                    error=ErrorDetails(
                        message="Operator not found",
                        type="not_found"
                    )
                )
            else:
                # Handle format differences between local and remote responses
                if options.remote:
                    # For remote responses, keep only the fields that Node.js returns
                    # Node.js remote response only has: arch, authors, description, name, os, tags, version
                    remote_fields = ["arch", "authors", "description", "name", "os", "tags", "version"]
                    filtered_data = {k: v for k, v in data_dict.items() if k in remote_fields}
                    data_dict = filtered_data
                    
                    # Keep string formats for remote responses (matches Node.js)
                    if isinstance(data_dict.get("authors"), str):
                        # Keep as string for remote responses (matches Node.js)
                        pass
                    if isinstance(data_dict.get("tags"), str):
                        # Keep as string for remote responses (matches Node.js)
                        pass
                else:
                    # For local responses, ensure proper array formats
                    if isinstance(data_dict.get("authors"), str):
                        # Convert string to array for local responses
                        authors_str = data_dict.get("authors", "")
                        if authors_str.startswith("[") and authors_str.endswith("]"):
                            # Parse string array format
                            authors_str = authors_str[1:-1]  # Remove brackets
                            data_dict["authors"] = [author.strip() for author in authors_str.split(",") if author.strip()]
                    
                    if isinstance(data_dict.get("tags"), str):
                        # Convert string to array for local responses
                        tags_str = data_dict.get("tags", "")
                        if tags_str.startswith("[") and tags_str.endswith("]"):
                            # Parse string array format
                            tags_str = tags_str[1:-1]  # Remove brackets
                            data_dict["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                
                if options.remote:
                    # For remote responses, create a minimal object with only the required fields
                    # Node.js remote response only has: arch, authors, description, name, os, tags, version
                    data = OperatorInfo(
                        name=data_dict.get("name", ""),
                        version=data_dict.get("version", ""),
                        description=data_dict.get("description", ""),
                        arch=data_dict.get("arch"),
                        os=data_dict.get("os"),
                        authors=data_dict.get("authors"),
                        tags=data_dict.get("tags")
                        # All other fields will be None/omitted
                    )
                else:
                    # For local responses, use the full object
                    data = OperatorInfo(**data_dict)
                
                response = OperatorInfoResponse(
                    status=ResponseStatus.SUCCESS,
                    message=response_data.get("message", "Operator info retrieved successfully"),
                    data=data
                )
                
                # For remote responses, customize the data serialization to exclude None fields
                if options.remote and hasattr(response.data, 'model_dump'):
                    # Get the data dict and filter out None values
                    data_dict = response.data.model_dump()
                    filtered_data = {k: v for k, v in data_dict.items() if v is not None}
                    
                    # Create a new response with filtered data
                    class FilteredOperatorInfo:
                        def __init__(self, data_dict):
                            for key, value in data_dict.items():
                                setattr(self, key, value)
                    
                    response.data = FilteredOperatorInfo(filtered_data)
                
                return response
        else:
            return OperatorInfoResponse(
                status=ResponseStatus.ERROR,
                message=response_data.get("message", "Failed to get operator info"),
                data=None,
                error=ErrorDetails(
                    message=response_data.get("message", "Unknown error"),
                    type="bridge_error"
                )
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return OperatorInfoResponse(
            status=ResponseStatus.ERROR,
            message="Failed to parse response from operator registry",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="json_parse_error"
            )
        )
    except Exception as e:
        logger.error(f"Info operation failed: {e}")
        return OperatorInfoResponse(
            status=ResponseStatus.ERROR,
            message="Failed to get operator info",
            data=None,
            error=ErrorDetails(
                message=str(e),
                type="bridge_error"
            )
        )
