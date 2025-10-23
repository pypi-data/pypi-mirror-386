"""
Exception classes for the SW Registry Stack Python SDK.

This module provides comprehensive error handling with specific exception types
for different error scenarios encountered in the SDK.
"""

from typing import Any, Dict, Optional


class SdkError(Exception):
    """
    Base exception class for all SDK-specific errors.
    
    This is the parent class for all custom exceptions raised by the SDK.
    It provides structured error information including error type, context,
    and maintains proper stack trace information.
    """
    
    def __init__(
        self,
        message: str,
        error_type: str = "sdk_error",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize SDK error.
        
        Args:
            message: Human-readable error message
            error_type: Type classification of the error
            context: Additional context information about the error
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.context = context or {}
        
        # Maintain proper stack trace
        if hasattr(Exception, '__cause__'):
            self.__cause__ = None


class ValidationError(SdkError):
    """
    Exception raised when input validation fails.
    
    This exception is raised when user-provided input fails validation
    checks, such as invalid parameter formats, missing required fields,
    or out-of-range values.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Name of the field that failed validation
            value: Value that failed validation
            context: Additional context information
        """
        error_context = context or {}
        if field is not None:
            error_context["field"] = field
        if value is not None:
            error_context["value"] = value
            
        super().__init__(message, "validation_error", error_context)


class FfiBridgeError(SdkError):
    """
    Exception raised when FFI bridge operations fail.
    
    This exception is raised when there are issues communicating with
    the native C++ libraries through the FFI bridge, such as library
    loading failures, function call errors, or memory management issues.
    """
    
    def __init__(
        self,
        message: str,
        function_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize FFI bridge error.
        
        Args:
            message: Human-readable error message
            function_name: Name of the FFI function that failed
            parameters: Parameters passed to the failed function
            context: Additional context information
        """
        error_context = context or {}
        if function_name is not None:
            error_context["function_name"] = function_name
        if parameters is not None:
            error_context["parameters"] = parameters
            
        super().__init__(message, "ffi_bridge_error", error_context)


class ConfigurationError(SdkError):
    """
    Exception raised when configuration is invalid or missing.
    
    This exception is raised when there are issues with SDK configuration,
    such as invalid paths, missing required configuration values, or
    incompatible configuration options.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            config_value: Configuration value that caused the error
            context: Additional context information
        """
        error_context = context or {}
        if config_key is not None:
            error_context["config_key"] = config_key
        if config_value is not None:
            error_context["config_value"] = config_value
            
        super().__init__(message, "configuration_error", error_context)


class CliExecutionError(SdkError):
    """
    Exception raised when CLI command execution fails.
    
    This exception is raised when there are issues executing CLI commands,
    such as command not found, execution timeouts, or non-zero exit codes.
    """
    
    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        args: Optional[list] = None,
        exit_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize CLI execution error.
        
        Args:
            message: Human-readable error message
            command: CLI command that failed
            args: Command arguments
            exit_code: Command exit code
            context: Additional context information
        """
        error_context = context or {}
        if command is not None:
            error_context["command"] = command
        if args is not None:
            error_context["args"] = args
        if exit_code is not None:
            error_context["exit_code"] = exit_code
            
        super().__init__(message, "cli_execution_error", error_context)


def is_sdk_error(error: Exception) -> bool:
    """
    Check if an exception is an SDK error.
    
    Args:
        error: Exception to check
        
    Returns:
        True if the error is an SDK error, False otherwise
    """
    return isinstance(error, SdkError)


def format_error(error: Exception) -> str:
    """
    Format an error for logging or display.
    
    Args:
        error: Error to format
        
    Returns:
        Formatted error string
    """
    if is_sdk_error(error):
        sdk_error = error  # type: SdkError
        context_str = ""
        if sdk_error.context:
            context_str = f" (Context: {sdk_error.context})"
        return f"{sdk_error.__class__.__name__}: {sdk_error.message}{context_str}"
    
    return f"{error.__class__.__name__}: {str(error)}"
