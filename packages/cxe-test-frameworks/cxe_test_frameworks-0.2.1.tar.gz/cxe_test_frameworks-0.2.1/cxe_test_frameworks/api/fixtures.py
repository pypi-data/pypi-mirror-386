"""
pytest Fixtures for API Testing

Provides reusable pytest fixtures for API testing across CXE services.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Iterator

import pytest
import snowflake.connector

from ..utils.configurations import load_toml
from .client import CXEApiClient

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = "constants/config.toml"


def pytest_addoption(parser: pytest.Parser):
    """Adds command-line options to pytest."""
    parser.addoption(
        "--env",
        action="store",
        default="local",
        help="Specify the environment to run tests against (e.g., local, sandbox, prod)",
    )
    parser.addoption(
        "--config",
        action="store",
        default=DEFAULT_CONFIG_PATH,
        help="Specify the path to the TOML configuration file",
    )


@pytest.fixture(scope="session")
def env(request: pytest.FixtureRequest) -> str:
    """Returns the environment specified by the --env command-line option."""
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def config_path(request: pytest.FixtureRequest) -> str:
    """Returns the path to the config file specified by --config or default."""
    return request.config.getoption("--config")


@pytest.fixture(scope="session")
def app_config(config_path: str) -> Dict:
    """
    Parses the TOML config file and returns the configuration object as a dictionary.

    Args:
        config_path (str): Path to the TOML configuration file

    Returns:
        Dict: Configuration dictionary
    """
    return load_toml(Path(config_path))


@pytest.fixture(scope="session")
def api_client(base_url: str, app_config: Dict[str, Any]) -> Iterator[CXEApiClient]:
    """
    Creates a session-based API client for making requests.

    This ensures that the connection is reused across multiple test functions,
    which can improve performance.

    Args:
        base_url (str): Base URL for the API
        app_config (Dict): Application configuration

    Returns:
        CXEApiClient: Configured API client
    """
    # Get API settings from config
    api_settings = app_config.get("api_settings", {})
    timeout = api_settings.get("timeout", 30)
    token_env = api_settings.get("snowflake_session_token_env", "SNOWHOUSE_SESSION_TOKEN")

    client = CXEApiClient(base_url, timeout=timeout, snowflake_token_env=token_env)

    yield client

    client.close()


@pytest.fixture(scope="session")
def snowflake_session_ctx(
    app_config: Dict[str, Any],
) -> Iterator[snowflake.connector.SnowflakeConnection]:
    """
    Establishes and provides a session-scoped Snowflake connection.

    Uses parameters from the '[snowflake_connection_params.default]' table in config.toml.

    Args:
        app_config (Dict): Application configuration

    Yields:
        SnowflakeConnection: Active Snowflake connection
    """
    sf_params_table = app_config.get("snowflake_connection_params")
    if not isinstance(sf_params_table, dict):
        raise ValueError("Missing 'snowflake_connection_params' table in config.toml")

    sf_details = sf_params_table.get("default")
    if not isinstance(sf_details, dict):
        raise ValueError(  # noqa: E501
            "Missing 'default' connection details under 'snowflake_connection_params' in config.toml"  # noqa: E501
        )

    # Ensure all required parameters are present
    required_keys = ["account", "user", "warehouse", "database", "schema", "role"]
    for key in required_keys:
        if key not in sf_details:
            raise ValueError(
                f"Missing required Snowflake connection parameter '{key}' in config.toml"
            )

    conn = None
    try:
        conn = snowflake.connector.connect(**sf_details)
        logger.info("Snowflake connection established")
        yield conn
    finally:
        if conn:
            conn.close()
            logger.info("Snowflake connection closed")


def pytest_sessionstart(session: pytest.Session):
    """
    Called after the Session object has been created and before running tests.
    Used to configure root logger for the test session.
    """
    log_level_str = (session.config.getoption("log_level") or "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)-8s] %(name)-30s [%(funcName)-20s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress verbose logging from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)

    logger.info(f"Logging configured for test session with level: {log_level_str}")
