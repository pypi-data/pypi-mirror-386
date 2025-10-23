"""
Executor configuration DTOs.

This module defines the configuration classes for the Executor service,
including validation and default values.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from pathlib import Path


class ExecutorConfig(BaseModel):
    """Configuration for the Executor service."""
    
    # Required paths
    base_path: str = Field(..., description="Base path for executor operations")
    bridge_lib_path: str = Field(..., description="Path to the executor bridge library")
    
    # Optional paths
    executor_path: Optional[str] = Field(
        default=None, 
        description="Path to executor CLI binary"
    )
    working_directory: Optional[str] = Field(
        default=None,
        description="Default working directory"
    )
    log_directory: Optional[str] = Field(
        default=None,
        description="Default log directory"
    )
    
    # Execution options
    timeout: int = Field(
        default=300,
        ge=1,
        description="Default timeout in seconds"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug logging"
    )
    pretty: bool = Field(
        default=False,
        description="Enable pretty printing"
    )
    use_ffi: bool = Field(
        default=True,
        description="Use FFI bridge instead of CLI"
    )
    
    # Bridge configuration
    bridge_lib_key: str = Field(
        default="executor_bridge",
        description="FFI bridge library key"
    )
    
    class Config:
        validate_by_name = True
        extra = "forbid"
    
    @validator('base_path')
    def validate_base_path(cls, v):
        """Validate base path exists or can be created."""
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create base path '{v}': {e}")
        return str(path.absolute())
    
    @validator('bridge_lib_path')
    def validate_bridge_lib_path(cls, v):
        """Validate bridge library path exists."""
        if not Path(v).exists():
            raise ValueError(f"Bridge library not found: {v}")
        return str(Path(v).absolute())
    
    @validator('executor_path')
    def validate_executor_path(cls, v):
        """Validate executor path if provided."""
        if v is not None and not Path(v).exists():
            raise ValueError(f"Executor binary not found: {v}")
        return v
    
    def model_dump_for_bridge(self) -> Dict[str, Any]:
        """Get configuration data suitable for bridge operations."""
        return {
            "basePath": self.base_path,
            "executorPath": self.executor_path,
            "workingDirectory": self.working_directory,
            "logDirectory": self.log_directory,
            "timeout": self.timeout,
            "debug": self.debug,
            "pretty": self.pretty,
            "useFfi": self.use_ffi,
            "bridgeLibPath": self.bridge_lib_path,
            "bridgeLibKey": self.bridge_lib_key
        }