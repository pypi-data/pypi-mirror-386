"""
SW Registry Stack Python SDK

A production-quality Python SDK for the SW Registry Stack, providing seamless
integration with Operator Registry, Pipeline Registry, Executor, and Recorder services.
"""

__version__ = "1.0.0"
__author__ = "SW Registry Stack Team"
__email__ = "team@sw-registry-stack.com"

# Core service classes
from .modules.operator_registry import OperatorRegistry
from .modules.pipeline_registry import PipelineRegistry
from .modules.executor import Executor
from .modules.recorder import Recorder

# Exception classes
from .exceptions import (
    SdkError,
    ValidationError,
    FfiBridgeError,
    ConfigurationError,
    CliExecutionError,
)

# Common types and utilities
from .shared.dto import (
    BaseConfig,
    CliResponse,
    ErrorDetails,
    PaginationOptions,
    OperationOptions,
    Platform,
    VersionInfo,
)

# Version information
__all__ = [
    # Core services
    "OperatorRegistry",
    "PipelineRegistry", 
    "Executor",
    "Recorder",
    # Exceptions
    "SdkError",
    "ValidationError",
    "FfiBridgeError",
    "ConfigurationError",
    "CliExecutionError",
    # Types
    "BaseConfig",
    "CliResponse",
    "ErrorDetails",
    "PaginationOptions",
    "OperationOptions",
    "Platform",
    "VersionInfo",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
