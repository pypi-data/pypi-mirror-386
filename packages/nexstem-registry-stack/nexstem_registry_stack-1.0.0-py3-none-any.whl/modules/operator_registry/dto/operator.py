"""
Operator entity DTO for Operator Registry.

This module provides the Operator data model used throughout
the Operator Registry operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Operator(BaseModel):
    """Operator entity model."""
    
    name: str = Field(..., description="Operator name")
    version: str = Field(..., description="Operator version")
    platform: str = Field(..., description="Target platform")
    install_path: str = Field(..., description="Installation path")
    description: str = Field(..., description="Operator description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
