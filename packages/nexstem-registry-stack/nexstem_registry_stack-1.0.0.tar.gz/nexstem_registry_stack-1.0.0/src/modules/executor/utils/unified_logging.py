"""
Unified logging system for Python SDK.

This module provides a unified logging interface that captures logs from all components
(SDK, Executor, C++ Nodes) with a consistent structure.
"""

from enum import IntEnum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import time
import json


class LOG_LEVELS(IntEnum):
    """Log levels for unified logging."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class LOG_SOURCES(IntEnum):
    """Log sources for unified logging."""
    NODE = 0
    EXECUTOR = 1
    PIPELINE = 2
    SDK = 3
    SYSTEM = 4


@dataclass
class UnifiedLogEntry:
    """Unified log entry structure."""
    node_id: str
    pipeline_id: str
    run_id: str
    device_id: str
    level: LOG_LEVELS
    source: LOG_SOURCES
    message: str
    timestamp: int  # Milliseconds since epoch
    elapsed_ms: int  # Milliseconds since pipeline start
    function_name: str
    file_name: str
    line_number: int
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    # Additional fields for SDK-specific context
    sdk_component: Optional[str] = None
    sdk_operation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'node_id': self.node_id,
            'pipeline_id': self.pipeline_id,
            'run_id': self.run_id,
            'device_id': self.device_id,
            'level': int(self.level),
            'source': int(self.source),
            'message': self.message,
            'timestamp': self.timestamp,
            'elapsed_ms': self.elapsed_ms,
            'function_name': self.function_name,
            'file_name': self.file_name,
            'line_number': self.line_number,
            'data': self.data,
            'metadata': self.metadata,
            'sdk_component': self.sdk_component,
            'sdk_operation': self.sdk_operation
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# Type alias for unified logging callback
UnifiedLoggingCallback = Callable[[UnifiedLogEntry], None]


class UnifiedLoggingService:
    """Service for managing unified logging callbacks and context."""
    
    def __init__(self):
        self.callbacks: list[UnifiedLoggingCallback] = []
        self.pipeline_context = {
            'pipeline_id': '',
            'run_id': '',
            'device_id': '',
            'pipeline_start_time': 0,
        }
    
    def add_callback(self, callback: UnifiedLoggingCallback) -> None:
        """Add a unified logging callback."""
        self.callbacks.append(callback)
    
    def set_pipeline_context(self, pipeline_id: str, run_id: str, device_id: str) -> None:
        """Set pipeline context for unified logging."""
        self.pipeline_context = {
            'pipeline_id': pipeline_id,
            'run_id': run_id,
            'device_id': device_id,
            'pipeline_start_time': int(time.time() * 1000),  # Convert to milliseconds
        }
    
    def log(self, entry: Dict[str, Any]) -> None:
        """Log a unified log entry."""
        # Fill in missing context
        full_entry = UnifiedLogEntry(
            node_id=entry.get('node_id', ''),
            pipeline_id=entry.get('pipeline_id', self.pipeline_context['pipeline_id']),
            run_id=entry.get('run_id', self.pipeline_context['run_id']),
            device_id=entry.get('device_id', self.pipeline_context['device_id']),
            level=entry.get('level', LOG_LEVELS.INFO),
            source=entry.get('source', LOG_SOURCES.SDK),
            message=entry.get('message', ''),
            timestamp=entry.get('timestamp', int(time.time() * 1000)),
            elapsed_ms=entry.get('elapsed_ms', 
                               int(time.time() * 1000) - self.pipeline_context['pipeline_start_time']),
            function_name=entry.get('function_name', ''),
            file_name=entry.get('file_name', ''),
            line_number=entry.get('line_number', 0),
            data=entry.get('data', {}),
            metadata=entry.get('metadata', {}),
            sdk_component=entry.get('sdk_component'),
            sdk_operation=entry.get('sdk_operation')
        )
        
        # Dispatch to all callbacks
        for callback in self.callbacks:
            try:
                callback(full_entry)
            except Exception as e:
                print(f"Error in unified logging callback: {e}")
    
    def log_sdk(self, component: str, operation: str, message: str, 
                level: LOG_LEVELS = LOG_LEVELS.INFO, data: Dict[str, Any] = None) -> None:
        """Log SDK operation."""
        if data is None:
            data = {}
            
        self.log({
            'source': LOG_SOURCES.SDK,
            'level': level,
            'message': message,
            'data': data,
            'sdk_component': component,
            'sdk_operation': operation,
            'function_name': operation,
            'file_name': 'executor.py',  # Example
            'line_number': 0,  # Placeholder
        })
    
    def log_pipeline(self, operation: str, message: str, 
                     level: LOG_LEVELS = LOG_LEVELS.INFO, data: Dict[str, Any] = None) -> None:
        """Log pipeline operation."""
        if data is None:
            data = {}
            
        self.log({
            'source': LOG_SOURCES.PIPELINE,
            'level': level,
            'message': message,
            'data': data,
            'sdk_component': 'PipelineManager',
            'sdk_operation': operation,
        })


# Global unified logging service instance
unified_logging_service = UnifiedLoggingService()
