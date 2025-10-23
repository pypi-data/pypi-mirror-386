"""
Options DTOs for Recorder operations.

This module defines the options classes used for various Recorder operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.dto.common import OperationOptions


class RecorderListOptions(OperationOptions):
    """Options for listing recordings."""
    
    order_by: Optional[str] = Field(
        default="createdAt",
        alias="orderBy",
        description="Field to order by"
    )
    order: Optional[str] = Field(
        default="DESC",
        description="Order direction (ASC or DESC)"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of recordings to return (0 for all)"
    )
    offset: Optional[int] = Field(
        default=None,
        description="Number of recordings to skip"
    )
    device_ids: Optional[List[str]] = Field(
        default=None,
        alias="deviceIds",
        description="List of device IDs to filter by"
    )
    subject_names: Optional[List[str]] = Field(
        default=None,
        alias="subjectNames",
        description="List of subject names to filter by"
    )
    subject_ids: Optional[List[str]] = Field(
        default=None,
        alias="subjectIds",
        description="List of subject IDs to filter by"
    )


class RecorderCreateOptions(OperationOptions):
    """Options for creating recordings matching Node.js format exactly."""
    
    name: str = Field(
        description="Recording name"
    )
    file_path: str = Field(
        alias="filePath",
        description="File path for the recording"
    )
    device_id: Optional[str] = Field(
        default=None,
        alias="deviceId",
        description="Device ID"
    )
    subject: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Subject information"
    )
    graph: Optional[str] = Field(
        default=None,
        description="Graph configuration"
    )
    channels: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of channels"
    )
    filters: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of filters"
    )
    markers: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of markers"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata"
    )
    
    class Config:
        validate_by_name = True


class RecorderUpdateOptions(OperationOptions):
    """Options for updating recordings."""
    
    name: Optional[str] = Field(
        default=None,
        description="Recording name"
    )
    subject: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Subject information"
    )
    graph: Optional[str] = Field(
        default=None,
        description="Graph configuration"
    )
    channels: Optional[List[str]] = Field(
        default=None,
        description="List of channels"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter configuration"
    )
    markers: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of markers"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Recording notes"
    )


class RecorderDownloadOptions(OperationOptions):
    """Options for downloading recordings."""
    
    destination: str = Field(
        description="Destination path for download"
    )
    format: Optional[str] = Field(
        default=None,
        description="Download format"
    )
    compression: Optional[bool] = Field(
        default=False,
        description="Whether to compress the download"
    )
