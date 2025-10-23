# Spyglass AI MCP Server

The Spyglass AI MCP server provides a simple interface for LLMs to query the Spyglass AI agent. The agent analyzes your telemetry data and provides intelligent insights about application performance, errors, and bottlenecks.

To install the MCP server for Cursor click the button below. It should open Cursor and prompt you to add your API Key.


[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=spyglass-AI&config=eyJlbnYiOnsiU1BZR0xBU1NfQVBJX0tFWSI6InlvdXIta2V5LWhlcmUifSwiY29tbWFuZCI6InV2IHJ1biBzcHlnbGFzcy1tY3AifQ%3D%3D)
 
Alternatively, add the following to your `~/.cursor/mcp.json` file (create it if you need to) and substitute your Spyglass API Key. Then restart Cursor to apply the change.
```json
{
  "mcpServers": {
    "spyglass-ai": {
      "command": "uv",
      "args": ["run", "spyglass-mcp"],
      "env": {
        "SPYGLASS_API_KEY": "your-key-here"
      }
    }
  }
}
```

Note that you need to have `uv` installed first, see the docs for that [here](https://docs.astral.sh/uv/getting-started/installation/)

## Available Tools

### `call_spyglass_agent`

Calls the Spyglass AI agent with a natural language query about your telemetry data.

**Parameters:**
- `query` (string, required): Natural language query about your application's telemetry data

**Example queries:**
- "What are the slowest endpoints in the last hour?"
- "Show me all errors in the checkout service"
- "Which services have the highest error rate?"
- "What's causing high latency in my API?"
- "How many requests has my app had in the last day?"

**Returns:**
- Natural language analysis of the telemetry data


## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPYGLASS_API_KEY` | Yes | N/A | API Key for authentication with Spyglass agent |
| `SPYGLASS_AGENT_ENDPOINT` | No | `https://agent.spyglass-ai.com` | Agent endpoint URL (useful for local testing) |

### Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--endpoint` | No | `https://agent.spyglass-ai.com` | Spyglass agent endpoint URL |
| `--transport` | No | `stdio` | Transport type (stdio or http) |
| `--port` | No | `8000` | Port for HTTP transport |

## Example: Using with an MCP Client

```python
import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def analyze():
    async with client:
        result = await client.call_tool("call_spyglass_agent", {
            "query": "What are the slowest endpoints?"
        })
        print(result)

asyncio.run(analyze())
```

## Logging

The MCP server logs to both stderr (captured by Cursor) and a file for debugging:

**Log file location:**
```
~/.spyglass/logs/mcp-server-YYYYMMDD.log
```

**View logs in real-time:**
```bash
tail -f ~/.spyglass/logs/mcp-server-$(date +%Y%m%d).log
```

The logs include:
- Server startup and configuration
- Incoming queries and responses
- API call details (with truncated tokens for security)
- Error messages and stack traces

## Development

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Setup

1. Clone the repository and navigate to the project directory:
```bash
cd spyglass-mcp
```

2. Install dependencies:
```bash
uv sync
```

This will create a virtual environment and install all required dependencies.

3. Copy the example environment file and configure your API key:
```bash
cp env.example .env
# Edit .env and add your SPYGLASS_API_KEY
```

### Running Locally

Run the MCP server in stdio mode (default):
```bash
uv run spyglass-mcp
```

Run with a custom endpoint (useful for testing against a local agent):
```bash
uv run spyglass-mcp --endpoint http://localhost:8080
```

Run in HTTP transport mode:
```bash
uv run spyglass-mcp --transport http --port 8000
```

### Running Tests

Run all tests:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run a specific test file:
```bash
uv run pytest tests/test_mcp_server.py
```

Run tests with coverage:
```bash
uv run pytest --cov=spyglass_mcp --cov-report=term-missing
```

### Building

Build the package for distribution:
```bash
uv build
```

This will create wheel and source distribution files in the `dist/` directory.

### Project Structure

```
spyglass-mcp/
├── .github/
│   └── workflows/
│       └── publish.yaml
├── src/
│   └── spyglass_mcp/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_mcp_server.py
├── CHANGELOG.md
├── env.example
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock
```
