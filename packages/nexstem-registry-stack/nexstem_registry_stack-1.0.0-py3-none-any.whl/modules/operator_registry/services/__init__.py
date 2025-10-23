"""
Services for Operator Registry operations.

This module provides service functions for all Operator Registry operations,
following the same structure as the Node.js SDK.
"""

from .list_service import list_operators
from .info_service import get_operator_info

__all__ = [
    "list_operators",
    "get_operator_info",
]
