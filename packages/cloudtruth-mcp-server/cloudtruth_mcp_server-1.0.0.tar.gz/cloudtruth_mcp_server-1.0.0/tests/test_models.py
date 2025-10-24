"""Tests for data models"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from cloudtruth_mcp.models import (
    CacheEntry,
    Environment,
    Parameter,
    ParameterType,
    Project,
    ServerConfig,
    Value,
)


class TestServerConfig:
    """Tests for ServerConfig model"""

    def test_valid_config(self):
        """Test valid configuration"""
        config = ServerConfig(
            api_key="test1234567890.ABCDEFGHIJKLMNOP",
            api_base_url="https://api.cloudtruth.io",
            default_project="my-app",
            default_environment="development",
        )
        assert config.api_key == "test1234567890.ABCDEFGHIJKLMNOP"
        assert config.api_base_url == "https://api.cloudtruth.io"
        assert config.default_project == "my-app"
        assert config.cache_ttl_seconds == 300  # Default

    def test_invalid_api_key_pattern(self):
        """Test API key validation"""
        with pytest.raises(ValidationError):
            ServerConfig(api_key="invalid-key-with-dashes")

    def test_invalid_api_key_length(self):
        """Test API key minimum length"""
        with pytest.raises(ValidationError):
            ServerConfig(api_key="short")

    def test_https_required(self):
        """Test HTTPS validation"""
        with pytest.raises(ValidationError):
            ServerConfig(api_key="test1234567890.ABC", api_base_url="http://api.cloudtruth.io")

    def test_cache_ttl_bounds(self):
        """Test cache TTL bounds"""
        # Valid
        config = ServerConfig(api_key="test1234567890.ABC", cache_ttl_seconds=60)
        assert config.cache_ttl_seconds == 60

        # Too high
        with pytest.raises(ValidationError):
            ServerConfig(api_key="test1234567890.ABC", cache_ttl_seconds=4000)

        # Negative
        with pytest.raises(ValidationError):
            ServerConfig(api_key="test1234567890.ABC", cache_ttl_seconds=-1)

    def test_invalid_log_level(self):
        """Test log level validation"""
        with pytest.raises(ValidationError):
            ServerConfig(api_key="test1234567890.ABC", log_level="INVALID")

    def test_valid_log_levels(self):
        """Test all valid log levels"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = ServerConfig(api_key="test1234567890.ABC", log_level=level)
            assert config.log_level == level


class TestProject:
    """Tests for Project model"""

    def test_valid_project(self):
        """Test valid project creation"""
        project = Project(
            id="proj-123",
            url="https://api.cloudtruth.io/api/v1/projects/proj-123/",
            name="my-app",
            description="My application",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert project.id == "proj-123"
        assert project.name == "my-app"
        assert project.access_controlled is False  # Default
        assert project.role is None  # Default (API may return None)


class TestEnvironment:
    """Tests for Environment model"""

    def test_valid_environment(self):
        """Test valid environment creation"""
        env = Environment(
            id="env-123",
            url="https://api.cloudtruth.io/api/v1/environments/env-123/",
            name="production",
            description="Production environment",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert env.id == "env-123"
        assert env.name == "production"
        assert env.children == []  # Default

    def test_environment_with_parent(self):
        """Test environment with parent"""
        env = Environment(
            id="env-123",
            url="https://api.cloudtruth.io/api/v1/environments/env-123/",
            name="staging",
            description="Staging environment",
            parent="https://api.cloudtruth.io/api/v1/environments/env-456/",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert env.parent is not None


class TestParameter:
    """Tests for Parameter model"""

    def test_valid_parameter(self):
        """Test valid parameter creation"""
        param = Parameter(
            id="param-123",
            url="https://api.cloudtruth.io/api/v1/parameters/param-123/",
            name="DATABASE_URL",
            description="Database connection string",
            secret=True,
            type=ParameterType.STRING,
            project="https://api.cloudtruth.io/api/v1/projects/proj-123/",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert param.id == "param-123"
        assert param.name == "DATABASE_URL"
        assert param.secret is True
        assert param.type == ParameterType.STRING


class TestValue:
    """Tests for Value model"""

    def test_valid_value(self):
        """Test valid value creation"""
        value = Value(
            id="val-123",
            url="https://api.cloudtruth.io/api/v1/values/val-123/",
            environment="https://api.cloudtruth.io/api/v1/environments/env-123/",
            environment_name="production",
            parameter="https://api.cloudtruth.io/api/v1/parameters/param-123/",
            internal_value="postgres://localhost:5432/mydb",
            value="postgres://localhost:5432/mydb",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert value.id == "val-123"
        assert value.environment_name == "production"
        assert value.secret is False  # Default

    def test_value_with_null_values(self):
        """Test value creation with null internal_value and value (unset parameter)"""
        value = Value(
            id="val-456",
            url="https://api.cloudtruth.io/api/v1/values/val-456/",
            environment="https://api.cloudtruth.io/api/v1/environments/env-123/",
            environment_name="production",
            parameter="https://api.cloudtruth.io/api/v1/parameters/param-456/",
            internal_value=None,  # Can be null if parameter not set
            value=None,  # Can be null if parameter not set
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
        )
        assert value.id == "val-456"
        assert value.internal_value is None
        assert value.value is None


class TestCacheEntry:
    """Tests for CacheEntry model"""

    def test_cache_entry_not_expired(self):
        """Test cache entry not expired"""
        entry = CacheEntry(
            key="test-key",
            value={"data": "value"},
            created_at=datetime.utcnow(),
            ttl_seconds=300,
        )
        assert not entry.is_expired
        assert entry.age_seconds < 1

    def test_cache_entry_expired(self):
        """Test cache entry expired"""
        entry = CacheEntry(
            key="test-key",
            value={"data": "value"},
            created_at=datetime.utcnow() - timedelta(seconds=400),
            ttl_seconds=300,
        )
        assert entry.is_expired
        assert entry.age_seconds > 300

    def test_cache_entry_expires_at(self):
        """Test expires_at property"""
        created = datetime.utcnow()
        entry = CacheEntry(
            key="test-key",
            value={"data": "value"},
            created_at=created,
            ttl_seconds=300,
        )
        expected_expiry = created + timedelta(seconds=300)
        assert abs((entry.expires_at - expected_expiry).total_seconds()) < 1
