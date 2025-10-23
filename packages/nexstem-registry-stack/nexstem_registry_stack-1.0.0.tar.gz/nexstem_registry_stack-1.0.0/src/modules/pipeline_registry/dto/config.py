"""
Configuration DTOs for Pipeline Registry operations.

This module defines the configuration classes used for Pipeline Registry operations.
"""

from typing import Optional
from pydantic import BaseModel, Field
from shared.dto.common import BaseConfig


class PipelineRegistryConfig(BaseConfig):
    """Configuration for Pipeline Registry operations."""
    
    base_path: str = Field(
        default="/opt/pipelines",
        description="Base path for pipeline operations"
    )
    bridge_lib_path: str = Field(
        description="Path to the pipeline registry bridge library"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    timeout: int = Field(
        default=5000,
        description="Timeout for operations in milliseconds"
    )
    registry_url: Optional[str] = Field(
        default=None,
        description="Remote registry URL"
    )
    registry_token: Optional[str] = Field(
        default=None,
        description="Registry authentication token"
    )
    max_concurrent_operations: int = Field(
        default=10,
        description="Maximum number of concurrent operations"
    )
    cache_size: int = Field(
        default=1000,
        description="Cache size for operations"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
