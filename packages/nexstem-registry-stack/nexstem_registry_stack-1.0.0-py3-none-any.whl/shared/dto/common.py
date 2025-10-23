"""
Common DTOs for the SW Registry Stack Python SDK.

This module provides common data transfer objects used across all services.
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"


class ErrorTypes(str, Enum):
    """Standard error type classifications."""
    VALIDATION_ERROR = "validation_error"
    FFI_BRIDGE_ERROR = "ffi_bridge_error"
    CONFIGURATION_ERROR = "configuration_error"
    CLI_EXECUTION_ERROR = "cli_execution_error"
    EXECUTION_ERROR = "execution_error"


class Platform(BaseModel):
    """Platform specification for cross-platform operations."""
    
    os: str = Field(..., description="Operating system (e.g., 'linux', 'darwin', 'windows')")
    arch: str = Field(..., description="Architecture (e.g., 'amd64', 'arm64', 'x86_64')")
    
    @validator('os')
    def validate_os(cls, v: str) -> str:
        """Validate operating system value."""
        valid_os = {'linux', 'darwin', 'windows', 'freebsd', 'openbsd'}
        if v.lower() not in valid_os:
            raise ValueError(f"Invalid OS: {v}. Must be one of {valid_os}")
        return v.lower()
    
    @validator('arch')
    def validate_arch(cls, v: str) -> str:
        """Validate architecture value."""
        valid_arch = {'amd64', 'arm64', 'x86_64', 'i386', 'armv7', 'ppc64le'}
        if v.lower() not in valid_arch:
            raise ValueError(f"Invalid architecture: {v}. Must be one of {valid_arch}")
        return v.lower()


class VersionInfo(BaseModel):
    """Version information structure."""
    
    version: str = Field(..., description="Version string (e.g., '1.0.0')")
    name: str = Field(..., description="Service name")
    build: Optional[str] = Field(None, description="Build information")
    commit: Optional[str] = Field(None, description="Git commit hash")


class ErrorDetails(BaseModel):
    """Error details structure for failed operations."""
    
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type classification")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class CliResponse(BaseModel, Generic[T]):
    """Standard CLI response format used by all services."""
    
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Human-readable message describing the result")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[ErrorDetails] = Field(None, description="Error details if status is 'error'")


class PaginationOptions(BaseModel):
    """Pagination options for list operations."""
    
    page: Optional[int] = Field(None, ge=1, description="Page number (1-based)")
    page_size: Optional[int] = Field(None, ge=1, le=1000, description="Number of items per page")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of items to return")
    
    @validator('page', 'page_size', 'limit')
    def validate_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that pagination values are positive."""
        if v is not None and v <= 0:
            raise ValueError("Pagination values must be positive")
        return v


class OperationOptions(BaseModel):
    """Common operation options."""
    
    timeout: Optional[int] = Field(None, ge=1000, le=300000, description="Request timeout in milliseconds")
    pretty: Optional[bool] = Field(None, description="Pretty print JSON output")
    debug: Optional[bool] = Field(None, description="Enable debug mode")


class BaseConfig(BaseModel):
    """Base configuration options for all services."""
    
    base_path: Optional[str] = Field(None, description="Base path for local operations")
    bridge_lib_path: Optional[str] = Field(None, description="Path to the native bridge library")
    timeout: Optional[int] = Field(30000, ge=1000, le=300000, description="Request timeout in milliseconds")
    debug: Optional[bool] = Field(False, description="Enable debug mode for additional logging")
    pretty: Optional[bool] = Field(False, description="Pretty print JSON output")
    
    @validator('base_path')
    def validate_base_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate base path."""
        if v is not None and not v.strip():
            raise ValueError("Base path cannot be empty")
        return v
    
    @validator('bridge_lib_path')
    def validate_bridge_lib_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate bridge library path."""
        if v is not None and not v.strip():
            raise ValueError("Bridge library path cannot be empty")
        return v
