"""
FastMCP server for Spyglass AI agent
"""

import argparse
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx
from fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Default endpoint
DEFAULT_ENDPOINT = "https://agent.spyglass-ai.com"

# Global variables for configuration
AGENT_ENDPOINT = DEFAULT_ENDPOINT
API_KEY = None


# Configure logging
def setup_logging():
    """Setup logging to both stderr and file"""
    # Create logs directory in user's home
    log_dir = Path.home() / ".spyglass" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    log_file = log_dir / f"mcp-server-{datetime.now().strftime('%Y%m%d')}.log"

    # Configure logger
    logger = logging.getLogger("spyglass_mcp")
    logger.setLevel(logging.INFO)

    # Console handler (stderr - captured by Cursor)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


logger = setup_logging()

# Initialize FastMCP server
mcp = FastMCP("Spyglass Agent MCP Server")


async def _call_spyglass_agent_impl(
    query: str, api_key: str | None, endpoint: str
) -> str:
    """
    Core implementation for calling the Spyglass AI agent.

    This function is extracted for testability.

    Args:
        query: Natural language query about telemetry data
        api_key: API key for authentication
        endpoint: Agent endpoint URL

    Returns:
        Analysis result from the Spyglass AI agent
    """
    logger.info(
        f"Received query: {query[:100]}..."
        if len(query) > 100
        else f"Received query: {query}"
    )

    if not api_key:
        logger.error("API key not configured")
        return "Error: API key not configured. Please set SPYGLASS_API_KEY environment variable."

    # Build the request payload (only query is needed, tenant_id comes from JWT)
    payload = {
        "query": query,
    }

    # Make the API call
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Calling Spyglass agent at {endpoint}")
            logger.debug(f"Request payload: {payload}")

            response = await client.post(
                f"{endpoint}/api/v1/agent/analyze",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            logger.info(f"Received response with status code: {response.status_code}")
            response.raise_for_status()

            # Parse and return the analysis
            result = response.json()
            analysis = result.get("analysis", "No analysis returned")

            logger.info(
                f"Analysis completed successfully, length: {len(analysis)} chars"
            )
            logger.debug(f"Analysis: {analysis}")

            return analysis

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")

            # Handle 403 (token limit exceeded) with a user-friendly message
            if e.response.status_code == 403:
                return "You are out of tokens for this month. Please upgrade your plan or wait until next month to continue."

            # Handle other HTTP errors
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", e.response.text)
                return f"Error: HTTP {e.response.status_code} - {error_detail}"
            except Exception:
                return f"Error: HTTP {e.response.status_code} - {e.response.text}"

        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return f"Error: Request failed - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"


@mcp.tool
async def call_spyglass_agent(query: str) -> str:
    """
    Call the Spyglass AI agent with a natural language query about your telemetry data.

    Args:
        query: Natural language query about telemetry data (e.g., "What are the slowest endpoints?")

    Returns:
        Analysis result from the Spyglass AI agent
    """
    return await _call_spyglass_agent_impl(query, API_KEY, AGENT_ENDPOINT)


def main():
    """Main entry point for CLI"""
    global AGENT_ENDPOINT, API_KEY

    # Read endpoint from environment variable, falling back to default
    env_endpoint = os.getenv("SPYGLASS_AGENT_ENDPOINT", DEFAULT_ENDPOINT)

    parser = argparse.ArgumentParser(description="Spyglass MCP Server")
    parser.add_argument(
        "--endpoint",
        default=env_endpoint,
        help=f"Spyglass agent endpoint URL (env: SPYGLASS_AGENT_ENDPOINT, default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http"],
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )

    args = parser.parse_args()

    logger.info("Starting Spyglass MCP Server")
    logger.info(f"Transport: {args.transport}")
    if args.transport == "http":
        logger.info(f"Port: {args.port}")

    # Read API key from environment variable
    API_KEY = os.getenv("SPYGLASS_API_KEY")
    if not API_KEY:
        logger.error("SPYGLASS_API_KEY environment variable is not set")
        print(
            "Error: SPYGLASS_API_KEY environment variable is required", file=sys.stderr
        )
        print(
            "Please set it with: export SPYGLASS_API_KEY='your-jwt-token'",
            file=sys.stderr,
        )
        exit(1)

    logger.info(f"API key configured (length: {len(API_KEY)} chars)")

    # Set the global configuration
    AGENT_ENDPOINT = args.endpoint
    logger.info(f"Agent endpoint: {AGENT_ENDPOINT}")

    # Run the server
    logger.info("MCP server starting...")
    try:
        if args.transport == "http":
            mcp.run(transport="http", port=args.port)
        else:
            mcp.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
