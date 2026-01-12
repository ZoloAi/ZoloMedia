"""
Pytest configuration and shared fixtures for zlsp tests.
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_zolo_file():
    """Create a temporary .zolo file for testing."""
    def _create_file(content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.zolo', delete=False) as f:
            f.write(content)
            return f.name
    return _create_file


@pytest.fixture
def sample_zolo_content():
    """Provide sample .zolo content for testing."""
    return """# Sample Configuration
app_name: TestApp
version: 1.0.0

server:
  host: localhost
  port(int): 8080
  ssl(bool): true

features:
  analytics(bool): true
  debug(bool): false
"""


@pytest.fixture
def invalid_zolo_content():
    """Provide invalid .zolo content for error testing."""
    return """port(int): not_a_number
enabled(bool): invalid_value
list: [unclosed
"""


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
