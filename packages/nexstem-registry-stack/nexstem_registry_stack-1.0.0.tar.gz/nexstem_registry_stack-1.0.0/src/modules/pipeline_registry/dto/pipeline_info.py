"""
Pipeline Info data model for Pipeline Registry operations.

This module defines the PipelineInfo data model used in Pipeline Registry info operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Node(BaseModel):
    """Node data model."""
    
    id: str = Field(description="Node ID")
    name: Optional[str] = Field(default=None, description="Node name")
    type: str = Field(description="Node type")
    version: str = Field(description="Node version")
    ref: Optional[str] = Field(default=None, description="Reference for pipeline nodes")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Node configuration")
    defaultConfig: Optional[Dict[str, Any]] = Field(default=None, description="Default configuration")
    module_path: Optional[str] = Field(default=None, description="Module path")
    input_types: Optional[List[str]] = Field(default=None, description="Input types")
    output_types: Optional[List[str]] = Field(default=None, description="Output types")
    parameters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Parameters")
    signals: Optional[List[Dict[str, Any]]] = Field(default=None, description="Signals")


class Pipe(BaseModel):
    """Pipe data model."""
    
    id: str = Field(description="Pipe ID")
    source: str = Field(description="Source node")
    destination: str = Field(description="Destination node")


class PipelineInfo(BaseModel):
    """Pipeline info data model matching Node.js format exactly."""
    
    authors: List[str] = Field(description="Pipeline authors")
    description: str = Field(description="Pipeline description")
    id: str = Field(description="Pipeline ID")
    install_path: Optional[str] = Field(default=None, description="Installation path")
    installed_at: Optional[str] = Field(default=None, description="Installation timestamp")
    name: str = Field(description="Pipeline name")
    nodes: List[Node] = Field(description="Pipeline nodes")
    pipes: List[Pipe] = Field(description="Pipeline pipes")
    signalSocketIdentifier: Optional[str] = Field(default=None, description="Signal socket identifier")
    tags: List[str] = Field(description="Pipeline tags")
    version: str = Field(description="Pipeline version")
    
    class Config:
        validate_by_name = True
        json_encoders = {
            # Add any custom encoders if needed
        }
