"""
Pytest configuration and fixtures for the SW Registry Stack Python SDK.
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from sw_registry_stack import OperatorRegistry
from sw_registry_stack.modules.operator_registry.dto import OperatorRegistryConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_bridge_lib_path():
    """Mock bridge library path for testing."""
    return "/mock/path/to/liboperator_registry_bridge.dylib"


@pytest.fixture
def operator_registry_config(mock_bridge_lib_path, temp_dir):
    """Create a test configuration for Operator Registry."""
    return OperatorRegistryConfig(
        base_path=temp_dir,
        bridge_lib_path=mock_bridge_lib_path,
        debug=True,
        timeout=5000
    )


@pytest.fixture
def mock_bridge():
    """Create a mock bridge for testing."""
    bridge = Mock()
    bridge.is_loaded.return_value = True
    bridge.load.return_value = None
    bridge.unload.return_value = None
    return bridge


@pytest.fixture
def operator_registry(operator_registry_config, mock_bridge):
    """Create an Operator Registry instance with mocked bridge."""
    with patch('sw_registry_stack.modules.operator_registry.operator_registry.OperatorRegistryBridge', return_value=mock_bridge):
        registry = OperatorRegistry(operator_registry_config)
        registry._is_initialized = True
        return registry


@pytest.fixture
def sample_operator_list_response():
    """Sample operator list response for testing."""
    return {
        "status": "success",
        "message": "Operators listed successfully",
        "data": {
            "count": 2,
            "operators": [
                {
                    "name": "signalgenerator",
                    "version": "1.0.0",
                    "platform": "linux/amd64",
                    "install_path": "/opt/operators/signalgenerator/1.0.0",
                    "description": "Signal generator operator",
                    "metadata": {"author": "test"}
                },
                {
                    "name": "consumer",
                    "version": "1.0.0",
                    "platform": "linux/amd64",
                    "install_path": "/opt/operators/consumer/1.0.0",
                    "description": "Consumer operator",
                    "metadata": {"author": "test"}
                }
            ]
        }
    }


@pytest.fixture
def sample_operator_install_response():
    """Sample operator install response for testing."""
    return {
        "status": "success",
        "message": "Operator installed successfully",
        "data": {
            "name": "signalgenerator",
            "version": "1.0.0",
            "platform": "linux/amd64",
            "action": "installed"
        }
    }


@pytest.fixture
def sample_operator_info_response():
    """Sample operator info response for testing."""
    return {
        "status": "success",
        "message": "Operator info retrieved successfully",
        "data": {
            "name": "signalgenerator",
            "version": "1.0.0",
            "platform": "linux/amd64",
            "install_path": "/opt/operators/signalgenerator/1.0.0",
            "description": "Signal generator operator",
            "metadata": {"author": "test"}
        }
    }


@pytest.fixture
def sample_error_response():
    """Sample error response for testing."""
    return {
        "status": "error",
        "message": "Operation failed",
        "data": None,
        "error": {
            "message": "Test error",
            "type": "test_error"
        }
    }
