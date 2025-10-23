"""
CPP Bridge implementations for Recorder operations.

This module provides individual bridge implementations for each recorder operation,
following the modular pattern used in operator registry and pipeline registry.
"""

from .list_bridge import ListBridge
from .create_bridge import CreateBridge
from .info_bridge import InfoBridge
from .update_bridge import UpdateBridge
from .start_bridge import StartBridge
from .stop_bridge import StopBridge
from .delete_bridge import DeleteBridge
from .download_bridge import DownloadBridge
from .duration_bridge import DurationBridge

__all__ = [
    "ListBridge",
    "CreateBridge", 
    "InfoBridge",
    "UpdateBridge",
    "StartBridge",
    "StopBridge",
    "DeleteBridge",
    "DownloadBridge",
    "DurationBridge"
]
