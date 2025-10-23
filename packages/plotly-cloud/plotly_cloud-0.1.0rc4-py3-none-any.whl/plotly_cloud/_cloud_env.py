"""Cloud environment configuration management for Plotly Cloud CLI."""

import os
from pathlib import Path

import tomli
from rich.console import Console

from .exceptions import CloudConfigError, EnvironmentError

console = Console()


class CloudConfig:
    """Manages cloud configuration for Plotly Cloud CLI."""

    def __init__(self):
        self._config_cache = None

    @property
    def config_path(self) -> Path:
        """Path to the cloud-env.toml configuration file."""
        return Path(__file__).parent / "cloud-env.toml"

    @property
    def config(self) -> dict:
        """Load and cache cloud configuration."""
        if self._config_cache is None:
            if not self.config_path.exists():
                raise CloudConfigError(
                    f"Cloud configuration not found at {self.config_path}",
                    "Configuration file is missing from the package.",
                )

            try:
                with open(self.config_path, "rb") as f:
                    self._config_cache = tomli.load(f)
            except Exception as e:
                raise CloudConfigError("Failed to load cloud configuration", str(e)) from e

        return self._config_cache

    def get_oauth_client_id(self) -> str:
        """Get OAuth client ID from configuration."""
        # Check environment variable first (overrides config file)
        client_id = os.getenv("PLOTLY_OAUTH_CLIENT_ID", "")
        if client_id:
            return client_id

        try:
            client_id = self.config.get("oauth_client_id", "")
            if client_id:
                return client_id
        except CloudConfigError:
            pass

        raise EnvironmentError("OAuth client ID not configured. Set 'oauth_client_id' in cloud-env.toml.")

    def get_api_base_url(self) -> str:
        """Get API base URL from configuration."""
        # Check environment variable first (overrides config file)
        api_url = os.getenv("PLOTLY_API_BASE_URL", "")
        if api_url:
            return api_url

        try:
            api_url = self.config.get("api_base_url", "")
            if api_url:
                return api_url
        except CloudConfigError:
            pass

        raise EnvironmentError("API base URL not configured. Set 'api_base_url' in cloud-env.toml.")

    def validate(self) -> bool:
        """Validate cloud configuration setup."""
        try:
            client_id = self.get_oauth_client_id()
            api_url = self.get_api_base_url()

            if not all([client_id, api_url]):
                console.print("✗ Incomplete cloud configuration")
                return False

            console.print("✓ Cloud configuration is valid")
            return True
        except (CloudConfigError, EnvironmentError) as e:
            console.print(f"✗ Configuration error: {e}")
            return False


# Global instance
cloud_config = CloudConfig()
