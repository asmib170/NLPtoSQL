"""Configuration provider interface and implementations.

Implementations:
  - FileConfigProvider: reads from a local JSON file (dev)
  - AwsConfigProvider: reads from AWS AppConfig / Secrets Manager (prod)
  - EnvConfigProvider: reads from environment variables (fallback)

Usage:
  The active provider is selected by the APP_ENV environment variable:
    APP_ENV=dev   → FileConfigProvider (reads config/dev.json)
    APP_ENV=prod  → AwsConfigProvider (reads from AWS)
    (default)     → FileConfigProvider with dev.json
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigProvider(ABC):
    """Abstract interface for loading configuration values.

    All config access goes through get() — implementations decide
    where the values come from (file, AWS, env vars, etc.)
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The config key (e.g. "MODEL_ID", "DB_PATH")
            default: Value to return if key is not found

        Returns:
            The config value, or default if not found.
        """
        ...

    @abstractmethod
    def get_all(self) -> dict[str, Any]:
        """Return all configuration as a dict."""
        ...


class FileConfigProvider(ConfigProvider):
    """Load configuration from a local JSON file.

    Used in development. Reads from config/<env>.json relative to the agent folder.
    """

    def __init__(self, config_path: str):
        self._path = config_path
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def get_all(self) -> dict[str, Any]:
        return dict(self._data)


class EnvConfigProvider(ConfigProvider):
    """Load configuration from environment variables.

    Used as a fallback or in containerized environments.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)

    def get_all(self) -> dict[str, Any]:
        return dict(os.environ)


class AwsConfigProvider(ConfigProvider):
    """Load configuration from AWS AppConfig or Secrets Manager.

    Used in production on AWS. Reads a JSON config document from
    AWS AppConfig (or SSM Parameter Store / Secrets Manager).

    To implement:
      1. Set APP_CONFIG_APP, APP_CONFIG_ENV, APP_CONFIG_PROFILE env vars
      2. Or set SSM_PARAMETER_NAME for SSM Parameter Store
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        # Option 1: AWS AppConfig
        # import boto3
        # client = boto3.client("appconfig", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        # response = client.get_configuration(
        #     Application=os.environ["APP_CONFIG_APP"],
        #     Environment=os.environ["APP_CONFIG_ENV"],
        #     Configuration=os.environ["APP_CONFIG_PROFILE"],
        #     ClientId="nlptosql-agent",
        # )
        # self._data = json.loads(response["Content"].read())

        # Option 2: SSM Parameter Store
        # import boto3
        # client = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        # response = client.get_parameter(
        #     Name=os.environ["SSM_PARAMETER_NAME"],
        #     WithDecryption=True,
        # )
        # self._data = json.loads(response["Parameter"]["Value"])

        raise NotImplementedError(
            "AwsConfigProvider not yet implemented. "
            "Uncomment the appropriate section above and install boto3."
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def get_all(self) -> dict[str, Any]:
        return dict(self._data)


# ------------------------------------------------------------------ #
# Factory: select provider based on APP_ENV
# ------------------------------------------------------------------ #
_AGENT_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
_CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "config_files"


def get_config_provider() -> ConfigProvider:
    """Get the active config provider based on APP_ENV.

    APP_ENV=dev  → FileConfigProvider (config/dev.json)
    APP_ENV=prod → AwsConfigProvider
    (default)    → FileConfigProvider (config/dev.json)
    """
    env = os.environ.get("APP_ENV", "dev").lower()

    if env == "prod":
        return AwsConfigProvider()

    # Dev or any other env — use file
    config_file = _CONFIG_DIR / f"{env}.json"
    if not config_file.exists():
        config_file = _CONFIG_DIR / "dev.json"

    return FileConfigProvider(str(config_file))
