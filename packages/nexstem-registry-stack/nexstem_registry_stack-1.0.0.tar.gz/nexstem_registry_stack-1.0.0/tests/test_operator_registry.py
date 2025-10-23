"""
Test suite for the Operator Registry service.
"""

import json
import pytest
from unittest.mock import Mock, patch
from sw_registry_stack import OperatorRegistry
from sw_registry_stack.modules.operator_registry.dto import OperatorRegistryConfig
from sw_registry_stack.exceptions import (
    SdkError,
    ValidationError,
    FfiBridgeError,
    ConfigurationError,
)
from sw_registry_stack.modules.operator_registry.dto import (
    OperatorListOptions,
    OperatorInstallOptions,
    OperatorInfoOptions,
    ResponseStatus,
)


class TestOperatorRegistryConfig:
    """Test cases for OperatorRegistryConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = OperatorRegistryConfig()
        assert config.base_path == "/opt/operators"
        assert config.debug is False
        assert config.pretty is False
        assert config.timeout == 30000
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = OperatorRegistryConfig(
            base_path="/custom/path",
            debug=True,
            pretty=True,
            timeout=10000
        )
        assert config.base_path == "/custom/path"
        assert config.debug is True
        assert config.pretty is True
        assert config.timeout == 10000
    
    def test_config_validation(self):
        """Test configuration validation."""
        with pytest.raises(ValidationError):
            OperatorRegistryConfig(timeout=500)  # Too low
        
        with pytest.raises(ValidationError):
            OperatorRegistryConfig(timeout=400000)  # Too high


class TestOperatorRegistry:
    """Test cases for OperatorRegistry."""
    
    def test_initialization(self, operator_registry_config, mock_bridge):
        """Test OperatorRegistry initialization."""
        with patch('sw_registry_stack.operator_registry.OperatorRegistryBridge', return_value=mock_bridge):
            registry = OperatorRegistry(operator_registry_config)
            assert registry.config == operator_registry_config
            assert not registry._is_initialized
    
    def test_initialization_with_dict_config(self, mock_bridge):
        """Test initialization with dictionary config."""
        config_dict = {
            "base_path": "/test/path",
            "debug": True
        }
        with patch('sw_registry_stack.operator_registry.OperatorRegistryBridge', return_value=mock_bridge):
            registry = OperatorRegistry(config_dict)
            assert registry.config.base_path == "/test/path"
            assert registry.config.debug is True
    
    def test_initialization_failure(self, operator_registry_config):
        """Test initialization failure."""
        with patch('sw_registry_stack.operator_registry.OperatorRegistryBridge', side_effect=Exception("Bridge error")):
            with pytest.raises(ConfigurationError):
                OperatorRegistry(operator_registry_config)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, operator_registry):
        """Test successful initialization."""
        await operator_registry.initialize()
        assert operator_registry._is_initialized
        operator_registry.bridge.load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, operator_registry):
        """Test initialization when already initialized."""
        await operator_registry.initialize()
        await operator_registry.initialize()  # Should not call bridge.load again
        operator_registry.bridge.load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, operator_registry_config, mock_bridge):
        """Test initialization failure."""
        mock_bridge.load.side_effect = Exception("Load error")
        with patch('sw_registry_stack.operator_registry.OperatorRegistryBridge', return_value=mock_bridge):
            registry = OperatorRegistry(operator_registry_config)
            with pytest.raises(FfiBridgeError):
                await registry.initialize()
    
    @pytest.mark.asyncio
    async def test_close_success(self, operator_registry):
        """Test successful close."""
        await operator_registry.close()
        assert not operator_registry._is_initialized
        operator_registry.bridge.unload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_not_initialized(self, operator_registry):
        """Test close when not initialized."""
        operator_registry._is_initialized = False
        await operator_registry.close()
        operator_registry.bridge.unload.assert_not_called()
    
    def test_ensure_initialized(self, operator_registry):
        """Test ensure_initialized check."""
        operator_registry._is_initialized = False
        with pytest.raises(SdkError, match="not initialized"):
            operator_registry._ensure_initialized()
    
    def test_validate_name_version(self, operator_registry):
        """Test name@version validation."""
        # Valid format
        operator_registry._validate_name_version("test@1.0.0")
        
        # Invalid formats
        with pytest.raises(ValidationError):
            operator_registry._validate_name_version("invalid")
        
        with pytest.raises(ValidationError):
            operator_registry._validate_name_version("@1.0.0")
        
        with pytest.raises(ValidationError):
            operator_registry._validate_name_version("test@")
    
    def test_parse_name_version(self, operator_registry):
        """Test name@version parsing."""
        name, version = operator_registry._parse_name_version("test@1.0.0")
        assert name == "test"
        assert version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_list_success(self, operator_registry, sample_operator_list_response):
        """Test successful operator listing."""
        operator_registry.bridge.list_operators.return_value = json.dumps(sample_operator_list_response)
        
        result = await operator_registry.list()
        
        assert result.status == ResponseStatus.SUCCESS
        assert result.data.count == 2
        assert len(result.data.operators) == 2
        assert result.data.operators[0].name == "signalgenerator"
        operator_registry.bridge.list_operators.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_with_options(self, operator_registry, sample_operator_list_response):
        """Test operator listing with options."""
        operator_registry.bridge.list_operators_with_options.return_value = json.dumps(sample_operator_list_response)
        
        options = OperatorListOptions(
            remote=True,
            page=1,
            page_size=10,
            operator="test"
        )
        
        result = await operator_registry.list(options)
        
        assert result.status == ResponseStatus.SUCCESS
        operator_registry.bridge.list_operators_with_options.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            remote=True,
            page=1,
            page_size=10,
            operator_name="test",
            versions=False
        )
    
    @pytest.mark.asyncio
    async def test_list_error_response(self, operator_registry, sample_error_response):
        """Test operator listing with error response."""
        operator_registry.bridge.list_operators.return_value = json.dumps(sample_error_response)
        
        result = await operator_registry.list()
        
        assert result.status == ResponseStatus.ERROR
        assert result.data.count == 0
        assert len(result.data.operators) == 0
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_list_json_parse_error(self, operator_registry):
        """Test operator listing with JSON parse error."""
        operator_registry.bridge.list_operators.return_value = "invalid json"
        
        result = await operator_registry.list()
        
        assert result.status == ResponseStatus.ERROR
        assert "Failed to parse response" in result.message
    
    @pytest.mark.asyncio
    async def test_install_success(self, operator_registry, sample_operator_install_response):
        """Test successful operator installation."""
        operator_registry.bridge.install_operator.return_value = json.dumps(sample_operator_install_response)
        
        result = await operator_registry.install("signalgenerator@1.0.0")
        
        assert result.status == ResponseStatus.SUCCESS
        assert result.data.name == "signalgenerator"
        assert result.data.version == "1.0.0"
        assert result.data.action == "installed"
        operator_registry.bridge.install_operator.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            name="signalgenerator",
            version="1.0.0",
            platform=None,
            force=False
        )
    
    @pytest.mark.asyncio
    async def test_install_with_options(self, operator_registry, sample_operator_install_response):
        """Test operator installation with options."""
        operator_registry.bridge.install_operator.return_value = json.dumps(sample_operator_install_response)
        
        options = OperatorInstallOptions(
            platform="linux/arm64",
            force=True
        )
        
        result = await operator_registry.install("signalgenerator@1.0.0", options)
        
        assert result.status == ResponseStatus.SUCCESS
        operator_registry.bridge.install_operator.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            name="signalgenerator",
            version="1.0.0",
            platform="linux/arm64",
            force=True
        )
    
    @pytest.mark.asyncio
    async def test_install_invalid_name_version(self, operator_registry):
        """Test operator installation with invalid name@version."""
        with pytest.raises(ValidationError):
            await operator_registry.install("invalid")
    
    @pytest.mark.asyncio
    async def test_uninstall_success(self, operator_registry):
        """Test successful operator uninstallation."""
        response = {
            "status": "success",
            "message": "Operator uninstalled successfully",
            "data": {
                "name": "signalgenerator",
                "version": "1.0.0"
            }
        }
        operator_registry.bridge.uninstall_operator.return_value = json.dumps(response)
        
        result = await operator_registry.uninstall("signalgenerator", "1.0.0")
        
        assert result.status == ResponseStatus.SUCCESS
        assert result.data.name == "signalgenerator"
        assert result.data.version == "1.0.0"
        operator_registry.bridge.uninstall_operator.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            name="signalgenerator",
            version="1.0.0"
        )
    
    @pytest.mark.asyncio
    async def test_uninstall_missing_params(self, operator_registry):
        """Test operator uninstallation with missing parameters."""
        with pytest.raises(ValidationError):
            await operator_registry.uninstall("", "1.0.0")
        
        with pytest.raises(ValidationError):
            await operator_registry.uninstall("test", "")
    
    @pytest.mark.asyncio
    async def test_info_success(self, operator_registry, sample_operator_info_response):
        """Test successful operator info retrieval."""
        operator_registry.bridge.get_operator_info.return_value = json.dumps(sample_operator_info_response)
        
        result = await operator_registry.info("signalgenerator@1.0.0")
        
        assert result.status == ResponseStatus.SUCCESS
        assert result.data.name == "signalgenerator"
        assert result.data.version == "1.0.0"
        assert result.data.description == "Signal generator operator"
        operator_registry.bridge.get_operator_info.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            remote=False,
            name="signalgenerator",
            version="1.0.0"
        )
    
    @pytest.mark.asyncio
    async def test_info_with_remote_option(self, operator_registry, sample_operator_info_response):
        """Test operator info retrieval with remote option."""
        operator_registry.bridge.get_operator_info.return_value = json.dumps(sample_operator_info_response)
        
        options = OperatorInfoOptions(remote=True)
        result = await operator_registry.info("signalgenerator@1.0.0", options)
        
        assert result.status == ResponseStatus.SUCCESS
        operator_registry.bridge.get_operator_info.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            remote=True,
            name="signalgenerator",
            version="1.0.0"
        )
    
    @pytest.mark.asyncio
    async def test_status_not_implemented(self, operator_registry):
        """Test operator status (not implemented)."""
        with pytest.raises(SdkError, match="not yet implemented"):
            await operator_registry.status("signalgenerator@1.0.0")
    
    @pytest.mark.asyncio
    async def test_push_success(self, operator_registry, temp_dir):
        """Test successful operator push."""
        # Create a temporary tar file
        tar_path = f"{temp_dir}/test.tar.gz"
        with open(tar_path, "w") as f:
            f.write("test content")
        
        response = {
            "status": "success",
            "message": "Operator pushed successfully",
            "data": {
                "name": "signalgenerator",
                "version": "1.0.0",
                "action": "pushed"
            }
        }
        operator_registry.bridge.push_operator.return_value = json.dumps(response)
        
        result = await operator_registry.push("signalgenerator@1.0.0", tar_path)
        
        assert result.status == ResponseStatus.SUCCESS
        assert result.data.name == "signalgenerator"
        assert result.data.action == "pushed"
        operator_registry.bridge.push_operator.assert_called_once_with(
            base_path=operator_registry.config.base_path,
            name="signalgenerator",
            version="1.0.0",
            tar_path=tar_path,
            local_only=False
        )
    
    @pytest.mark.asyncio
    async def test_push_invalid_tar_path(self, operator_registry):
        """Test operator push with invalid tar path."""
        with pytest.raises(ValidationError):
            await operator_registry.push("signalgenerator@1.0.0", "/nonexistent/path.tar.gz")
    
    @pytest.mark.asyncio
    async def test_repair_not_implemented(self, operator_registry):
        """Test operator repair (not implemented)."""
        with pytest.raises(SdkError, match="not yet implemented"):
            await operator_registry.repair()
    
    def test_get_config(self, operator_registry, operator_registry_config):
        """Test getting configuration."""
        config = operator_registry.get_config()
        assert config == operator_registry_config
    
    def test_is_initialized(self, operator_registry):
        """Test checking initialization status."""
        assert operator_registry.is_initialized() is True
        operator_registry._is_initialized = False
        assert operator_registry.is_initialized() is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self, operator_registry_config, mock_bridge):
        """Test async context manager."""
        with patch('sw_registry_stack.operator_registry.OperatorRegistryBridge', return_value=mock_bridge):
            async with OperatorRegistry(operator_registry_config) as registry:
                assert registry._is_initialized
                mock_bridge.load.assert_called_once()
            
            mock_bridge.unload.assert_called_once()


class TestOperatorRegistryIntegration:
    """Integration tests for OperatorRegistry."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, operator_registry, sample_operator_list_response, sample_operator_install_response):
        """Test a complete workflow."""
        # Mock responses
        operator_registry.bridge.list_operators.return_value = json.dumps(sample_operator_list_response)
        operator_registry.bridge.install_operator.return_value = json.dumps(sample_operator_install_response)
        
        # List operators
        list_result = await operator_registry.list()
        assert list_result.status == ResponseStatus.SUCCESS
        assert list_result.data.count == 2
        
        # Install an operator
        install_result = await operator_registry.install("newoperator@2.0.0")
        assert install_result.status == ResponseStatus.SUCCESS
        assert install_result.data.action == "installed"
