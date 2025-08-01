"""Unit tests for data models and configuration structures."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.data_models import (
    SetupConfig, 
    OperationResult, 
    FileOperationConfig, 
    DownloadConfig,
    ConfigurationError,
    load_default_configuration,
    validate_configuration
)


class TestOperationResult:
    """Test cases for OperationResult dataclass."""
    
    def test_operation_result_basic(self):
        """Test basic OperationResult creation."""
        result = OperationResult(success=True, message="Test message")
        
        assert result.success is True
        assert result.message == "Test message"
        assert result.details is None
        assert result.suggestions == []
    
    def test_operation_result_with_details(self):
        """Test OperationResult with details."""
        result = OperationResult(
            success=False,
            message="Test message",
            details="Additional details"
        )
        
        assert result.success is False
        assert result.details == "Additional details"
    
    def test_operation_result_with_suggestions(self):
        """Test OperationResult with suggestions."""
        suggestions = ["Suggestion 1", "Suggestion 2"]
        result = OperationResult(
            success=False,
            message="Test message",
            suggestions=suggestions
        )
        
        assert result.suggestions == suggestions
    
    def test_operation_result_post_init(self):
        """Test OperationResult __post_init__ method."""
        result = OperationResult(success=True, message="Test", suggestions=None)
        
        # __post_init__ should set suggestions to empty list if None
        assert result.suggestions == []


class TestSetupConfig:
    """Test cases for SetupConfig dataclass."""
    
    def test_setup_config_creation(self):
        """Test SetupConfig creation with all parameters."""
        greenluma_path = Path("test/greenluma")
        koalageddon_path = Path("test/koalageddon")
        desktop_path = Path("test/desktop")
        
        config = SetupConfig(
            greenluma_path=greenluma_path,
            koalageddon_config_path=koalageddon_path,
            desktop_path=desktop_path,
            koalageddon_url="https://example.com/download.zip",
            required_exclusions=["path1", "path2"],
            app_id="123456"
        )
        
        assert config.greenluma_path == greenluma_path
        assert config.koalageddon_config_path == koalageddon_path
        assert config.desktop_path == desktop_path
        assert config.koalageddon_url == "https://example.com/download.zip"
        assert config.required_exclusions == ["path1", "path2"]
        assert config.app_id == "123456"
    
    def test_setup_config_create_default(self):
        """Test SetupConfig default creation."""
        config = SetupConfig.create_default()
        
        assert config.app_id == "252950"
        assert "GreenLuma" in str(config.greenluma_path)
        assert "Koalageddon" in str(config.koalageddon_config_path)
        assert "Desktop" in str(config.desktop_path)
        assert config.koalageddon_url.startswith("https://")
        assert len(config.required_exclusions) > 0
    
    def test_setup_config_from_file_not_found(self):
        """Test SetupConfig.from_file with non-existent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            SetupConfig.from_file("nonexistent.json")
    
    def test_setup_config_from_file_invalid_json(self):
        """Test SetupConfig.from_file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                SetupConfig.from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_setup_config_from_file_valid_jsonc(self):
        """Test SetupConfig.from_file with valid JSONC file."""
        jsonc_content = '''
        {
            // This is a comment
            "setup": {
                "app_id": "999999",
                "koalageddon_url": "https://custom.example.com/download.zip"
            }
        }
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonc', delete=False) as f:
            f.write(jsonc_content)
            temp_path = f.name
        
        try:
            config = SetupConfig.from_file(temp_path)
            assert config.app_id == "999999"
            assert config.koalageddon_url == "https://custom.example.com/download.zip"
            assert config.config_file_path == Path(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_setup_config_validate_success(self):
        """Test SetupConfig validation with valid configuration."""
        config = SetupConfig.create_default()
        result = config.validate()
        
        assert result.success is True
        assert "successful" in result.message.lower()
    
    def test_setup_config_validate_missing_required(self):
        """Test SetupConfig validation with missing required fields."""
        config = SetupConfig(
            greenluma_path=None,  # Missing required field
            koalageddon_config_path=Path("test"),
            desktop_path=Path("test"),
            koalageddon_url="",  # Empty required field
            required_exclusions=[]
        )
        
        result = config.validate()
        
        assert result.success is False
        assert "validation failed" in result.message.lower()
        assert len(result.suggestions) > 0
    
    def test_setup_config_validate_invalid_url(self):
        """Test SetupConfig validation with invalid URL."""
        config = SetupConfig.create_default()
        config.koalageddon_url = "invalid-url"
        
        result = config.validate()
        
        assert result.success is False
        assert "URL" in result.details
    
    def test_setup_config_to_dict(self):
        """Test SetupConfig conversion to dictionary."""
        config = SetupConfig.create_default()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'greenluma_path' in config_dict
        assert 'koalageddon_config_path' in config_dict
        assert 'desktop_path' in config_dict
        assert 'koalageddon_url' in config_dict
        assert 'required_exclusions' in config_dict
        assert 'app_id' in config_dict


class TestFileOperationConfig:
    """Test cases for FileOperationConfig dataclass."""
    
    def test_file_operation_config_creation(self):
        """Test FileOperationConfig creation."""
        config = FileOperationConfig(
            source_path=Path("source"),
            destination_path=Path("dest"),
            operation_type="copy"
        )
        
        assert config.source_path == Path("source")
        assert config.destination_path == Path("dest")
        assert config.operation_type == "copy"
        assert config.create_directories is True
        assert config.overwrite_existing is False
    
    def test_file_operation_config_validate_success(self):
        """Test FileOperationConfig validation with valid configuration."""
        config = FileOperationConfig(
            source_path=Path("source"),
            destination_path=Path("dest"),
            operation_type="extract"
        )
        
        result = config.validate()
        assert result.success is True
    
    def test_file_operation_config_validate_missing_source(self):
        """Test FileOperationConfig validation with missing source."""
        config = FileOperationConfig(
            source_path=None,
            destination_path=Path("dest"),
            operation_type="copy"
        )
        
        result = config.validate()
        assert result.success is False
        assert "source path" in result.message.lower()
    
    def test_file_operation_config_validate_invalid_operation(self):
        """Test FileOperationConfig validation with invalid operation type."""
        config = FileOperationConfig(
            source_path=Path("source"),
            destination_path=Path("dest"),
            operation_type="invalid"
        )
        
        result = config.validate()
        assert result.success is False
        assert "invalid operation type" in result.message.lower()


class TestDownloadConfig:
    """Test cases for DownloadConfig dataclass."""
    
    def test_download_config_creation(self):
        """Test DownloadConfig creation."""
        config = DownloadConfig(
            url="https://example.com/file.zip",
            destination_path=Path("downloads")
        )
        
        assert config.url == "https://example.com/file.zip"
        assert config.destination_path == Path("downloads")
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.chunk_size == 8192
    
    def test_download_config_validate_success(self):
        """Test DownloadConfig validation with valid configuration."""
        config = DownloadConfig(
            url="https://example.com/file.zip",
            destination_path=Path("downloads")
        )
        
        result = config.validate()
        assert result.success is True
    
    def test_download_config_validate_missing_url(self):
        """Test DownloadConfig validation with missing URL."""
        config = DownloadConfig(
            url="",
            destination_path=Path("downloads")
        )
        
        result = config.validate()
        assert result.success is False
        assert "URL is required" in result.message
    
    def test_download_config_validate_invalid_url(self):
        """Test DownloadConfig validation with invalid URL."""
        config = DownloadConfig(
            url="ftp://example.com/file.zip",
            destination_path=Path("downloads")
        )
        
        result = config.validate()
        assert result.success is False
        assert "HTTP or HTTPS" in result.message
    
    def test_download_config_validate_invalid_timeout(self):
        """Test DownloadConfig validation with invalid timeout."""
        config = DownloadConfig(
            url="https://example.com/file.zip",
            destination_path=Path("downloads"),
            timeout=-1
        )
        
        result = config.validate()
        assert result.success is False
        assert "timeout must be positive" in result.message.lower()


class TestConfigurationFunctions:
    """Test cases for configuration utility functions."""
    
    @patch('src.data_models.Path')
    def test_load_default_configuration_no_file(self, mock_path):
        """Test load_default_configuration when Config.jsonc doesn't exist."""
        mock_path.return_value.exists.return_value = False
        
        config = load_default_configuration()
        
        assert isinstance(config, SetupConfig)
        assert config.app_id == "252950"
    
    @patch('src.data_models.Path')
    @patch('builtins.open', mock_open(read_data='{"setup": {"app_id": "123456"}}'))
    def test_load_default_configuration_with_file(self, mock_path):
        """Test load_default_configuration when Config.jsonc exists."""
        mock_path.return_value.exists.return_value = True
        
        config = load_default_configuration()
        
        assert isinstance(config, SetupConfig)
    
    def test_validate_configuration(self):
        """Test validate_configuration function."""
        config = SetupConfig.create_default()
        result = validate_configuration(config)
        
        assert isinstance(result, OperationResult)
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__])