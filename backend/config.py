"""Configuration management for the application."""
import yaml
import os
from pathlib import Path

class Config:
    """Application configuration."""

    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found at {self.config_path}. "
                "Please copy config.yaml.template to config.yaml and configure it."
            )

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    @property
    def neo4j_uri(self) -> str:
        return self.config['neo4j']['uri']

    @property
    def neo4j_user(self) -> str:
        return self.config['neo4j']['user']

    @property
    def neo4j_password(self) -> str:
        return self.config['neo4j']['password']

    @property
    def app_host(self) -> str:
        return self.config['app']['host']

    @property
    def app_port(self) -> int:
        return self.config['app']['port']

    @property
    def app_debug(self) -> bool:
        return self.config['app']['debug']

    @property
    def items_per_page(self) -> int:
        return self.config['ui']['items_per_page']

    @property
    def default_view(self) -> str:
        return self.config['ui']['default_view']

# Global config instance
config = Config()
