"""Pytest configuration and fixtures for Spyglass MCP tests"""

import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_api_key():
    """Set a test API key for all tests."""
    os.environ["SPYGLASS_API_KEY"] = "test-api-key-for-testing"
    yield
    # Cleanup
    if "SPYGLASS_API_KEY" in os.environ:
        del os.environ["SPYGLASS_API_KEY"]


@pytest.fixture
def mock_analysis_response():
    """Sample analysis response from Spyglass agent."""
    return {
        "analysis": "The slowest endpoints in your application are:\n1. /api/checkout - 1.2s average\n2. /api/products - 800ms average\n3. /api/users - 500ms average"
    }
