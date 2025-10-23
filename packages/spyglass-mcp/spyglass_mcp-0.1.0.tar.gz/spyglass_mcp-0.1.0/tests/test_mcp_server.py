"""Tests for Spyglass MCP Server"""

import pytest
import respx
from httpx import Response
from spyglass_mcp.main import _call_spyglass_agent_impl, DEFAULT_ENDPOINT


@pytest.mark.asyncio
async def test_call_spyglass_agent_success(mock_analysis_response):
    """Test successful query to Spyglass agent via MCP server."""
    # Mock the HTTP call to the Spyglass agent
    with respx.mock:
        respx.post(
            f"{DEFAULT_ENDPOINT}/api/v1/agent/analyze",
        ).mock(return_value=Response(200, json=mock_analysis_response))

        # Call the tool implementation
        result = await _call_spyglass_agent_impl(
            "What are the slowest endpoints?", "test-api-key", DEFAULT_ENDPOINT
        )

        # Verify the response
        assert "slowest endpoints" in result.lower()
        assert "/api/checkout" in result
        assert "1.2s" in result


@pytest.mark.asyncio
async def test_call_spyglass_agent_no_api_key():
    """Test that error is returned when API key is not configured."""
    result = await _call_spyglass_agent_impl(
        "What are the slowest endpoints?", None, DEFAULT_ENDPOINT
    )

    assert "Error: API key not configured" in result
    assert "SPYGLASS_API_KEY" in result


@pytest.mark.asyncio
async def test_call_spyglass_agent_http_error():
    """Test error handling when agent returns HTTP error."""
    with respx.mock:
        respx.post(
            f"{DEFAULT_ENDPOINT}/api/v1/agent/analyze",
        ).mock(return_value=Response(500, json={"detail": "Internal server error"}))

        result = await _call_spyglass_agent_impl(
            "What are the slowest endpoints?", "test-api-key", DEFAULT_ENDPOINT
        )

        assert "Error: HTTP 500" in result
        assert "Internal server error" in result


@pytest.mark.asyncio
async def test_call_spyglass_agent_token_limit_exceeded():
    """Test user-friendly message when token limit is exceeded (403)."""
    with respx.mock:
        respx.post(
            f"{DEFAULT_ENDPOINT}/api/v1/agent/analyze",
        ).mock(return_value=Response(403, json={"detail": "Token limit exceeded"}))

        result = await _call_spyglass_agent_impl(
            "What are the slowest endpoints?", "test-api-key", DEFAULT_ENDPOINT
        )

        assert "out of tokens" in result.lower()
        assert "upgrade" in result.lower() or "month" in result.lower()


@pytest.mark.asyncio
async def test_call_spyglass_agent_network_error():
    """Test error handling when network request fails."""
    with respx.mock:
        respx.post(
            f"{DEFAULT_ENDPOINT}/api/v1/agent/analyze",
        ).mock(side_effect=Exception("Connection timeout"))

        result = await _call_spyglass_agent_impl(
            "What are the slowest endpoints?", "test-api-key", DEFAULT_ENDPOINT
        )

        assert "Error:" in result
