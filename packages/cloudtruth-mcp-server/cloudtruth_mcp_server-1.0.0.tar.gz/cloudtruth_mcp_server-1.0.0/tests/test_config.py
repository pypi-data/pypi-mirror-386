"""Tests for configuration management"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from cloudtruth_mcp.config import ConfigManager


class TestConfigManager:
    """Tests for ConfigManager"""

    def test_find_config_path_default(self):
        """Test default config path"""
        with patch.dict(os.environ, {}, clear=True):
            path = ConfigManager._find_config_path()
            expected = Path.home() / ".config" / "cloudtruth" / "mcp-config.json"
            assert path == expected

    def test_find_config_path_from_env(self):
        """Test config path from environment variable"""
        custom_path = "/custom/path/config.json"
        with patch.dict(os.environ, {"CLOUDTRUTH_CONFIG": custom_path}):
            path = ConfigManager._find_config_path()
            assert path == Path(custom_path)

    def test_load_config_file_not_found(self):
        """Test error when config file doesn't exist"""
        mgr = ConfigManager(Path("/nonexistent/config.json"))
        with pytest.raises(FileNotFoundError) as exc_info:
            mgr.load()
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_valid_config(self, tmp_path):
        """Test loading valid configuration"""
        config_file = tmp_path / "config.json"
        config_data = {
            "api_key": "test1234567890.ABCDEFGHIJKLMNOP",
            "api_base_url": "https://api.cloudtruth.io",
            "default_project": "my-app",
        }
        config_file.write_text(json.dumps(config_data))
        os.chmod(config_file, 0o600)

        mgr = ConfigManager(config_file)
        config = mgr.load()

        assert config.api_key == "test1234567890.ABCDEFGHIJKLMNOP"
        assert config.api_base_url == "https://api.cloudtruth.io"
        assert config.default_project == "my-app"

    def test_load_invalid_json(self, tmp_path):
        """Test error on invalid JSON"""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        mgr = ConfigManager(config_file)
        with pytest.raises(json.JSONDecodeError):
            mgr.load()

    def test_load_invalid_config_data(self, tmp_path):
        """Test error on invalid config data"""
        config_file = tmp_path / "config.json"
        config_data = {"api_key": "invalid-key-with-dashes"}  # Invalid characters
        config_file.write_text(json.dumps(config_data))

        mgr = ConfigManager(config_file)
        with pytest.raises(ValidationError):
            mgr.load()

    def test_insecure_permissions_warning(self, tmp_path, caplog):
        """Test warning for insecure permissions"""
        config_file = tmp_path / "config.json"
        config_data = {
            "api_key": "test1234567890.ABCDEFGHIJKLMNOP",
            "api_base_url": "https://api.cloudtruth.io",
        }
        config_file.write_text(json.dumps(config_data))
        os.chmod(config_file, 0o644)  # Insecure permissions

        mgr = ConfigManager(config_file)
        config = mgr.load()

        # Should load but with warning
        assert config is not None
        assert "insecure permissions" in caplog.text.lower()

    def test_get_config_cached(self, tmp_path):
        """Test get returns cached config"""
        config_file = tmp_path / "config.json"
        config_data = {
            "api_key": "test1234567890.ABCDEFGHIJKLMNOP",
            "api_base_url": "https://api.cloudtruth.io",
        }
        config_file.write_text(json.dumps(config_data))
        os.chmod(config_file, 0o600)

        mgr = ConfigManager(config_file)
        config1 = mgr.get()
        config2 = mgr.get()

        # Should be same object (cached)
        assert config1 is config2

    def test_reload_config(self, tmp_path):
        """Test reload refreshes config"""
        config_file = tmp_path / "config.json"
        config_data = {
            "api_key": "test1234567890.ABCDEFGHIJKLMNOP",
            "api_base_url": "https://api.cloudtruth.io",
            "cache_ttl_seconds": 300,
        }
        config_file.write_text(json.dumps(config_data))
        os.chmod(config_file, 0o600)

        mgr = ConfigManager(config_file)
        config1 = mgr.load()
        assert config1.cache_ttl_seconds == 300

        # Update file
        config_data["cache_ttl_seconds"] = 600
        config_file.write_text(json.dumps(config_data))

        config2 = mgr.reload()
        assert config2.cache_ttl_seconds == 600
