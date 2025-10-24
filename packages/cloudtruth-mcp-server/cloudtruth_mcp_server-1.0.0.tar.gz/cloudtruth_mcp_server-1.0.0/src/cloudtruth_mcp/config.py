"""Configuration management"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from .models import ServerConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages server configuration"""

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "cloudtruth" / "mcp-config.json"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._find_config_path()
        self.config: Optional[ServerConfig] = None

    @staticmethod
    def _find_config_path() -> Path:
        """Find configuration file"""
        # Check environment variable
        env_path = os.getenv("CLOUDTRUTH_CONFIG")
        if env_path:
            return Path(env_path)

        # Use default path
        return ConfigManager.DEFAULT_CONFIG_PATH

    def load(self) -> ServerConfig:
        """Load and validate configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create a configuration file with your CloudTruth API key.\n"
                f"Example:\n"
                f"  mkdir -p ~/.config/cloudtruth\n"
                f"  cat > ~/.config/cloudtruth/mcp-config.json << EOF\n"
                f"  {{\n"
                f'    "api_key": "YOUR-API-KEY-HERE",\n'
                f'    "api_base_url": "https://api.cloudtruth.io"\n'
                f"  }}\n"
                f"  EOF\n"
                f"  chmod 600 ~/.config/cloudtruth/mcp-config.json"
            )

        # Check file permissions
        self._check_permissions()

        # Load JSON
        with open(self.config_path) as f:
            config_data = json.load(f)

        # Validate with Pydantic
        self.config = ServerConfig(**config_data)
        return self.config

    def _check_permissions(self) -> None:
        """Check configuration file permissions"""
        stat_info = os.stat(self.config_path)
        mode = stat_info.st_mode & 0o777

        if mode not in [0o600, 0o400]:
            logger.warning(
                f"Configuration file has insecure permissions: {oct(mode)}. "
                f"Recommend: chmod 600 {self.config_path}"
            )

    def reload(self) -> ServerConfig:
        """Reload configuration from file"""
        return self.load()

    def get(self) -> ServerConfig:
        """Get current configuration (load if not loaded)"""
        if self.config is None:
            return self.load()
        return self.config
