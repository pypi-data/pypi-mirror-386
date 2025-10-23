"""
Operator Info entity DTO for Operator Registry.

This module provides the OperatorInfo data model used for
detailed operator information responses.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """Parameter definition for operators."""
    
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    default: Optional[Any] = Field(None, description="Default value")
    required: Optional[bool] = Field(False, description="Whether parameter is required")


class Signal(BaseModel):
    """Signal definition for operators."""
    
    name: str = Field(..., description="Signal name")
    description: str = Field(..., description="Signal description")
    parameters: List[Parameter] = Field(default_factory=list, description="Signal parameters")


class OutputType(BaseModel):
    """Output type definition for operators."""
    
    type: str = Field(..., description="Output type")
    properties: List[Dict[str, Any]] = Field(default_factory=list, description="Output properties")


class OperatorSchemas(BaseModel):
    """Schema definitions for different programming languages."""
    
    typescript: Optional[str] = Field(None, description="TypeScript schema file path")
    python: Optional[str] = Field(None, description="Python schema file path")
    cpp: Optional[str] = Field(None, description="C++ schema file path")


class OperatorInfo(BaseModel):
    """Detailed operator information model."""
    
    # Basic info
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")
    description: str = Field(..., description="Operator description")
    
    # Platform info
    arch: Optional[str] = Field(None, description="Architecture")
    os: Optional[str] = Field(None, description="Operating system")
    platform: Optional[str] = Field(None, description="Target platform")
    
    # Authors and metadata
    authors: Optional[Union[List[str], str]] = Field(None, description="Authors")
    created_at: Optional[str] = Field(None, description="Creation date")
    tags: Optional[Union[List[str], str]] = Field(None, description="Tags")
    
    # Installation info
    install_path: Optional[str] = Field(None, description="Installation path")
    installed_at: Optional[str] = Field(None, description="Installation timestamp")
    entrypoint: Optional[str] = Field(None, description="Entry point")
    module_path: Optional[str] = Field(None, description="Module path")
    
    # Type definitions
    input_types: Optional[List[Any]] = Field(None, description="Input types")
    output_types: Optional[List[OutputType]] = Field(None, description="Output types")
    
    # Parameters and signals
    parameters: Optional[List[Parameter]] = Field(None, description="Operator parameters")
    signals: Optional[List[Signal]] = Field(None, description="Operator signals")
    
    # Schema definitions
    schemas: Optional[OperatorSchemas] = Field(None, description="Schema definitions for different languages")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
