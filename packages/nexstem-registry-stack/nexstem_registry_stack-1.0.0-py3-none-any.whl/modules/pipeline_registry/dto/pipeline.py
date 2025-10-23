"""
Pipeline data model for Pipeline Registry operations.

This module defines the Pipeline data model used in Pipeline Registry operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Pipeline(BaseModel):
    """Pipeline data model matching Node.js format exactly."""
    
    description: str = Field(
        description="Pipeline description"
    )
    id: str = Field(
        description="Pipeline ID"
    )
    install_path: str = Field(
        alias="install_path",
        description="Installation path"
    )
    installed_at: str = Field(
        alias="installed_at",
        description="Installation timestamp"
    )
    name: str = Field(
        description="Pipeline name"
    )
    version: str = Field(
        description="Pipeline version"
    )
    
    class Config:
        validate_by_name = True
        json_encoders = {
            # Add any custom encoders if needed
        }
