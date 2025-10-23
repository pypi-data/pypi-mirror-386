"""
CXE API Client

Base API client with Snowflake authentication, retry logic, and logging
for testing CXE services.
"""

import logging
import os
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class CXEApiClient:
    """
    Base API client for CXE services with Snowflake authentication.

    Provides:
    - Snowflake token authentication
    - Session management for connection reuse
    - Logging of requests and responses
    - Standard HTTP methods
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        snowflake_token_env: str = "SNOWHOUSE_SESSION_TOKEN",
    ):
        """
        Initialize API client.

        Args:
            base_url (str): Base URL for the API
            timeout (int): Request timeout in seconds (default: 30)
            snowflake_token_env (str): Environment variable name for Snowflake token
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # Configure Snowflake authentication
        self._configure_snowflake_auth(snowflake_token_env)

        # Set common headers
        self.session.headers.update({"User-Agent": "cxe-test-commons/1.0"})

        logger.info(f"Initialized CXE API client for {base_url}")

    def _configure_snowflake_auth(self, token_env: str) -> None:
        """
        Configure Snowflake token authentication.

        Args:
            token_env (str): Environment variable name containing the session token
        """
        session_token = os.getenv(token_env)

        if session_token:
            self.session.headers.update({"Authorization": f'Snowflake Token="{session_token}"'})
            logger.info(f"Snowflake authentication configured using {token_env}")
        else:
            logger.warning(
                f"No Snowflake session token found in {token_env}. "
                f"Set it using: export {token_env}='your_token_here'"
            )

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Make GET request.

        Args:
            endpoint (str): API endpoint (will be appended to base_url)
            params (Dict, optional): Query parameters
            **kwargs: Additional arguments passed to requests.get

        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"GET {url}")

        response = self.session.get(
            url, params=params, timeout=kwargs.pop("timeout", self.timeout), **kwargs
        )

        logger.info(f"Response: {response.status_code}")
        return response

    def post(
        self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """
        Make POST request.

        Args:
            endpoint (str): API endpoint
            data (Dict, optional): Form data
            json (Dict, optional): JSON data
            **kwargs: Additional arguments passed to requests.post

        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"POST {url}")

        response = self.session.post(
            url, data=data, json=json, timeout=kwargs.pop("timeout", self.timeout), **kwargs
        )

        logger.info(f"Response: {response.status_code}")
        return response

    def put(
        self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """
        Make PUT request.

        Args:
            endpoint (str): API endpoint
            data (Dict, optional): Form data
            json (Dict, optional): JSON data
            **kwargs: Additional arguments passed to requests.put

        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"PUT {url}")

        response = self.session.put(
            url, data=data, json=json, timeout=kwargs.pop("timeout", self.timeout), **kwargs
        )

        logger.info(f"Response: {response.status_code}")
        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Make DELETE request.

        Args:
            endpoint (str): API endpoint
            **kwargs: Additional arguments passed to requests.delete

        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"DELETE {url}")

        response = self.session.delete(url, timeout=kwargs.pop("timeout", self.timeout), **kwargs)

        logger.info(f"Response: {response.status_code}")
        return response

    def patch(
        self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """
        Make PATCH request.

        Args:
            endpoint (str): API endpoint
            data (Dict, optional): Form data
            json (Dict, optional): JSON data
            **kwargs: Additional arguments passed to requests.patch

        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"PATCH {url}")

        response = self.session.patch(
            url, data=data, json=json, timeout=kwargs.pop("timeout", self.timeout), **kwargs
        )

        logger.info(f"Response: {response.status_code}")
        return response

    def close(self) -> None:
        """Close the session."""
        self.session.close()
        logger.info("API client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
