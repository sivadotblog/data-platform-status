"""
Shared test configuration and fixtures.

This module provides common fixtures and setup for all test modules
in the data platform status monitoring test suite.
"""

import os
import sys
import pytest

# Add project root to Python path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True)
def mock_env_base():
    """
    Base fixture to ensure environment variables are clean for each test.
    This runs automatically for all tests.
    """
    # Store existing environment variables
    existing_vars = {}
    env_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_TENANT_ID",
        "AZ_TOKEN",
    ]

    for var in env_vars:
        if var in os.environ:
            existing_vars[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore environment variables
    for var, value in existing_vars.items():
        os.environ[var] = value


@pytest.fixture
def mock_datetime(mocker):
    """Mock datetime to return a fixed time"""
    mock_dt = mocker.patch("datetime.datetime")
    mock_dt.utcnow.return_value.isoformat.return_value = "2024-02-07T00:00:00Z"
    return mock_dt


@pytest.fixture
def mock_requests(mocker):
    """Mock requests to prevent actual HTTP calls"""
    return mocker.patch("requests.get")


@pytest.fixture
def mock_requests_post(mocker):
    """Mock requests.post to prevent actual HTTP calls"""
    return mocker.patch("requests.post")


@pytest.fixture
def capsys_reset(capsys):
    """Reset captured output before each test"""
    capsys.readouterr()
    return capsys
