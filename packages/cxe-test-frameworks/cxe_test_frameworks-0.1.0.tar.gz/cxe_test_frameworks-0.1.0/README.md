# CXE Test Commons

Shared testing infrastructure for CXE services.

## Overview

This library provides common testing utilities extracted from production tests:
- **API Testing**: Client, fixtures, validators, constants
- **UI Testing**: BasePage, BaseElement, wait helpers, assertions
- **Utilities**: Logging configuration and JSON config utilities

## Installation

### From PyPI

```bash
pip install cxe-test-frameworks
```

### With Poetry

```bash
poetry add cxe-test-frameworks
```

Or in `pyproject.toml`:
```toml
[tool.poetry.dependencies]
cxe-test-frameworks = "^0.1.0"
```

### With requirements.txt

```txt
cxe-test-frameworks==0.1.0
```

### For Local Development

```bash
# Install in editable mode
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### API Testing

```python
from cxe_test_frameworks.api import CXEApiClient, HTTPStatusCodes, compare_nested_json_keys

# Create API client
client = CXEApiClient("http://localhost:8080/api/v1")

# Make requests
response = client.get("/endpoint")
assert response.status_code == HTTPStatusCodes.OK

# Use response validators
from cxe_test_frameworks.api import ResponseValidator

data = response.json()
ResponseValidator.validate_error_response(data)

# Compare JSON structures for schema validation
json_before = response1.text
json_after = response2.text
missing_keys = compare_nested_json_keys(json_before, json_after)
assert not missing_keys, f"Schema changed! Missing keys: {missing_keys}"
```

### UI Testing

```python
from cxe_test_frameworks.ui import BasePage, BaseElement

class MyPage(BasePage):
    @property
    def page_url(self):
        return "http://localhost:5173/my-page"

    @property
    def page_title(self):
        return "My Page Title"

    def verify_page_loaded(self):
        return self.verify_element_visible('[data-testid="main-content"]')

# Use in tests
def test_my_page(page):
    my_page = MyPage(page)
    my_page.navigate_to()
    assert my_page.verify_page_loaded()

# Or use BaseElement for enhanced interactions
def test_with_base_element(page):
    submit_btn = BaseElement(page, '[data-testid="submit"]', "Submit Button")
    submit_btn.wait_for_clickable().click().assert_visible()
```

### Logging and Configuration

```python
from cxe_test_frameworks.utils import get_logger, load_json, merge_configs
from pathlib import Path

# Get configured logger
logger = get_logger(__name__)
logger.info("Test started")

# Load and merge JSON configs
base = load_json(Path("config/base.json"))
env = load_json(Path("config/dev.json"))
config = merge_configs(base, env)
```

## What's Included

### API Module (`cxe_test_frameworks.api`)
- `CXEApiClient` - HTTP client with Snowflake authentication
- `HTTPStatusCodes` - HTTP status code constants
- `ResponseValidator` - Response validation utilities
- `compare_nested_json_keys` - JSON structure comparison for schema validation
- `parse_config` - TOML configuration parser
- `fixtures.py` - pytest fixtures for API testing

### UI Module (`cxe_test_frameworks.ui`)
- `BasePage` - Base page object with common methods
- `BaseElement` - Enhanced element wrapper with retry logic and method chaining
- `ElementFactory` - Factory for creating BaseElement instances
- `WaitHelpers` - Smart wait strategies
- `AssertionUtils` - Enhanced assertions

### Utils Module (`cxe_test_frameworks.utils`)
- `LoggerConfig` - Centralized logging configuration
- `get_logger` - Convenience function for getting loggers
- `load_json` - Load JSON files with error handling
- `merge_configs` - Deep merge configuration dictionaries
- `deep_update` - In-place deep merge
- `get_nested_value` - Access nested config with dot notation

## Usage in Projects

### For API Tests (Service Repositories)

```python
# conftest.py
from cxe_test_frameworks.api.fixtures import (
    pytest_addoption,
    env,
    config_path,
    app_config,
    api_client,
    snowflake_session_ctx,
    pytest_sessionstart
)

# Service-specific URL mapping
SOT_URLS = {
    "local": "http://localhost:8080/api/v1",
    "dev": "https://sot-dev.snowflakecomputing.app/api/v1",
}

@pytest.fixture(scope="session")
def base_url(env):
    """Get base URL for environment."""
    if env not in SOT_URLS:
        raise ValueError(f"Invalid environment: {env}")
    if SOT_URLS[env] == "TODO":
        raise ValueError(f"Environment {env} not configured")
    return SOT_URLS[env]
```

### For UI Tests (E2E)

```python
# pages/my_page.py
from cxe_test_frameworks.ui import BasePage

class MyServicePage(BasePage):
    def __init__(self, page, base_url):
        super().__init__(page, {"base_url": base_url})

    @property
    def page_url(self):
        return f"{self.config['base_url']}/my-page"

    @property
    def page_title(self):
        return "My Service Page"

    def verify_page_loaded(self):
        return self.verify_element_visible('[data-testid="page-header"]')
```

## Development

### Running Tests (for the library itself)

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=cxe_test_frameworks
```

### Code Quality

```bash
# Format code
black cxe_test_frameworks/

# Type checking
mypy cxe_test_frameworks/

# Linting
flake8 cxe_test_frameworks/
```

## Requirements

- **Python 3.11 or higher** (required for built-in `tomllib`)
- pytest 7.4.0+
- For API testing: requests, snowflake-connector-python
- For UI testing: playwright 1.40.0+
- For logging: structlog, colorlog
- For reporting: allure-pytest (for test reports)

## License

Proprietary - Snowflake Inc.

## Contributing

This library provides shared testing infrastructure. When adding new utilities:
1. Ensure they are truly generic (usable across multiple CXE services)
2. Keep service-specific code in service repos
3. Update this README with new functionality
4. Add tests for new utilities
5. Follow existing code style and patterns

## Support

For issues or questions:
- Check existing CXE service test repositories for usage examples
- Review the source code - it's well documented
- Contact the CXE team

## Version History

- **0.1.0** (2025-10-21) - Initial release
  - API testing: HTTP client, fixtures, validators, JSON schema comparison
  - UI testing: BasePage, BaseElement (method chaining), wait helpers, assertions
  - Utilities: Structured logging (structlog), JSON config utilities
  - Python 3.11+ (uses built-in tomllib)
  - Published to PyPI: `pip install cxe-test-frameworks`
