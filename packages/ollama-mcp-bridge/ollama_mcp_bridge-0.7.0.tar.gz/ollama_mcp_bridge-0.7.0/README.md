<p align="center">

  <img src="https://github.com/jonigl/ollama-mcp-bridge/raw/main/misc/ollama-mcp-bridge-logo-512.png" width="256" />
</p>
<p align="center">
<i>Provides an API layer in front of the Ollama API, seamlessly adding tools from multiple MCP servers so every Ollama request can access all connected tools transparently.</i>
</p>

# Ollama MCP Bridge

[![PyPI - Python Version](https://img.shields.io/pypi/v/ollama-mcp-bridge?label=ollama-mcp-bridge-pypi)](https://pypi.org/project/ollama-mcp-bridge/)
[![Tests](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/test.yml/badge.svg)](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/test.yml)
[![Test Publish](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/test-publish.yml/badge.svg)](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/test-publish.yml)
[![Publish](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/publish.yml/badge.svg)](https://github.com/jonigl/ollama-mcp-bridge/actions/workflows/publish.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Or, install from PyPI with pip](#or-install-from-pypi-with-pip)
  - [Or, run with Docker Compose](#or-run-with-docker-compose)
  - [Or, run with Docker only](#or-run-with-docker-only)
  - [Or, install from source](#or-install-from-source)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
  - [MCP Servers Configuration](#mcp-servers-configuration)
  - [CORS Configuration](#cors-configuration)
- [Usage](#usage)
  - [Start the Server](#start-the-server)
  - [CLI Options](#cli-options)
  - [API Usage](#api-usage)
  - [Example: Chat](#example-chat)
- [Development](#development)
  - [Key Dependencies](#key-dependencies)
  - [Testing](#testing)
- [Related Projects](#related-projects)
- [Inspiration and Credits](#inspiration-and-credits)

## Features

- 🚀 **Pre-loaded Servers**: All MCP servers are connected at startup from JSON configuration
- 📝 **JSON Configuration**: Configure multiple servers with complex commands and environments
- 🔗 **Tool Integration**: Automatic tool call processing and response integration
- 🔄 **Multi-Round Tool Execution**: Automatically loops through multiple rounds of tool calls until completion
- 🛡️ **Configurable Tool Limits**: Set maximum tool execution rounds to prevent excessive tool calls
- 🛠️ **All Tools Available**: Ollama can use any tool from any connected server simultaneously
- 🔌 **Complete API Compatibility**: `/api/chat` adds tools while all other Ollama API endpoints are transparently proxied
- 🔧 **Configurable Ollama**: Specify custom Ollama server URL via CLI (supports local and cloud models)
- ☁️ **Cloud Model Support**: Works with Ollama cloud models
- 🔄 **Version Check**: Automatic check for newer versions with upgrade instructions
- 🌊 **Streaming Responses**: Supports incremental streaming of responses to clients
- 🤔 **Thinking Mode**: Proxies intermediate "thinking" messages from Ollama and MCP tools
- ⚡️ **FastAPI Backend**: Modern async API with automatic documentation
- 🏗️ **Modular Architecture**: Clean separation into CLI, API, and MCP management modules
- 💻 **Typer CLI**: Clean command-line interface with configurable options
- 📊 **Structured Logging**: Uses loguru for comprehensive logging
- 📦 **PyPI Package**: Easily installable via pip or uv from PyPI
- 🗣️ **System Prompt Configuration**: Allows setting a system prompt for the assistant's behavior

## Requirements

- Python >= 3.10.15
- Ollama server running (local or remote)
- MCP server configuration file with at least one MCP server defined (see below for example)

## Installation

You can install `ollama-mcp-bridge` in several ways, depending on your preference:

### Quick Start
Install instantly with [uvx](https://github.com/astral-sh/uv):
```bash
uvx ollama-mcp-bridge
```

### Or, install from PyPI with pip
```bash
pip install --upgrade ollama-mcp-bridge
```

### Or, run with Docker Compose

```bash
docker-compose up
```

This uses the included [docker-compose.yml](./docker-compose.yml) file which:
- Builds the bridge from source using this Dockerfile [Dockerfile](./Dockerfile)
- Connects to Ollama running on the host machine (`host.docker.internal:11434`)
- Maps the configuration file from [./mcp-config.json](./mcp-config.json) (includes mock [weather server for demo](./mock-weather-mcp-server))
- Allows all CORS origins (configurable via `CORS_ORIGINS` environment variable)


### Or, install from source

```bash
# Clone the repository
git clone https://github.com/jonigl/ollama-mcp-bridge.git
cd ollama-mcp-bridge

# Install dependencies using uv
uv sync

# Start Ollama (if not already running)
ollama serve

# Run the bridge (preferred)
ollama-mcp-bridge
```

If you want to install the project in editable mode (for development):

```bash
# Install the project in editable mode
uv tool install --editable .
# Run it like this:
ollama-mcp-bridge
```

## How It Works

1. **Startup**: All MCP servers defined in the configuration are loaded and connected
2. **Version Check**: At startup, the bridge checks for newer versions and notifies if an update is available
3. **Tool Collection**: Tools from all servers are collected and made available to Ollama
4. **Chat Completion Request (`/api/chat` endpoint only)**: When a chat completion request is received on `/api/chat`:
   - The request is forwarded to Ollama (local or cloud) along with the list of all available tools
   - If Ollama chooses to invoke any tools, those tool calls are executed through the corresponding MCP servers
   - Tool responses are fed back to Ollama
   - The process repeats in a loop until no more tool calls are needed
   - Responses stream to the client in real-time throughout the entire process
   - The final response (with all tool results integrated) is returned to the client
   - **This is the only endpoint where MCP server tools are integrated.**
5. **Other Endpoints**: All other endpoints (except `/api/chat`, `/health`, and `/version`) are fully proxied to the underlying Ollama server with no modification.
6. **Logging**: All operations are logged using loguru for debugging and monitoring

## Configuration

### MCP Servers Configuration

Create an MCP configuration file at `mcp-config.json` with your servers:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "./mock-weather-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "MCP_LOG_LEVEL": "ERROR"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/tmp"
      ]
    }
  }
}
```

> [!WARNING]
> **Docker Command Limitations**: When running in Docker, MCP servers should use commands available in the container:
> - ✅ `npx` for Node.js-based MCP servers
> - ✅ `uvx` for Python-based MCP servers
> - ✅ Direct executables in the container
> - ❌ `docker` commands (unless Docker-in-Docker is configured)
> - ❌ Local file paths from your host machine

### CORS Configuration

Configure Cross-Origin Resource Sharing (CORS) to allow requests from your frontend applications:

```bash
# Allow all origins (default, not recommended for production)
ollama-mcp-bridge

# Allow specific origins
CORS_ORIGINS="http://localhost:3000,https://myapp.com" ollama-mcp-bridge

# Allow multiple origins with different ports
CORS_ORIGINS="http://localhost:3000,http://localhost:8080,https://app.example.com" ollama-mcp-bridge
```

**Environment Variables:**
- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: `*`)
  - `*` allows all origins (shows warning in logs)
  - Example: `CORS_ORIGINS="http://localhost:3000,https://myapp.com" ollama-mcp-bridge`
- `MAX_TOOL_ROUNDS`: Maximum number of tool execution rounds (default: unlimited)
  - Can be overridden with `--max-tool-rounds` CLI parameter (CLI takes precedence)
  - Example: `MAX_TOOL_ROUNDS=5 ollama-mcp-bridge`
- `OLLAMA_URL`: URL of the Ollama server (default: `http://localhost:11434`)
  - Can be overridden with `--ollama-url` CLI parameter
  - Useful for Docker deployments and configuration management
  - Example: `OLLAMA_URL=http://192.168.1.100:11434 ollama-mcp-bridge`
- `SYSTEM_PROMPT`: Optional system prompt to prepend to all forwarded `/api/chat` requests
  - Can be set via the `SYSTEM_PROMPT` environment variable or `--system-prompt` CLI flag
  - If provided, the bridge will prepend a system message (role: `system`) to the beginning of the `messages` array for `/api/chat` requests unless the request already starts with a system message.
  - Example: `SYSTEM_PROMPT="You are a concise assistant." ollama-mcp-bridge`

**CORS Logging:**
- The bridge logs CORS configuration at startup
- Shows warning when using `*` (all origins)
- Shows allowed origins when properly configured

> [!WARNING]
> Using `CORS_ORIGINS="*"` allows all origins and is not recommended for production. Always specify exact origins for security.

> [!NOTE]
> An example MCP server script is provided at [mock-weather-mcp-server/main.py](mock-weather-mcp-server/main.py).

## Usage

### Start the Server
```bash
# Start with default settings (config: ./mcp-config.json, host: 0.0.0.0, port: 8000)
ollama-mcp-bridge

# Start with custom configuration file
ollama-mcp-bridge --config /path/to/custom-config.json

# Custom host and port
ollama-mcp-bridge --host 0.0.0.0 --port 8080

# Custom Ollama server URL (local or cloud)
ollama-mcp-bridge --ollama-url http://192.168.1.100:11434

# Limit tool execution rounds (prevents excessive tool calls)
ollama-mcp-bridge --max-tool-rounds 5

# Set a system prompt to prepend to all /api/chat requests
ollama-mcp-bridge --system-prompt "You are a concise assistant."

# Combine options
ollama-mcp-bridge --config custom.json --host 0.0.0.0 --port 8080 --ollama-url http://remote-ollama:11434 --max-tool-rounds 10

# Check version and available updates
ollama-mcp-bridge --version
```

> [!TIP]
> If using `uvx` to run the bridge, you have to specify the command as `uvx ollama-mcp-bridge` instead of just `ollama-mcp-bridge`.

> [!NOTE]
> This bridge supports both streaming responses and thinking mode. You receive incremental responses as they are generated, with tool calls and intermediate thinking messages automatically proxied between Ollama and all connected MCP tools.

### CLI Options
- `--config`: Path to MCP configuration file (default: `mcp-config.json`)
- `--host`: Host to bind the server (default: `0.0.0.0`)
- `--port`: Port to bind the server (default: `8000`)
- `--ollama-url`: Ollama server URL (default: `http://localhost:11434`)
- `--max-tool-rounds`: Maximum tool execution rounds (default: unlimited)
- `--reload`: Enable auto-reload during development
- `--version`: Show version information, check for updates and exit
- `--system-prompt`: Optional system prompt to prepend to `/api/chat` requests (default: none)
### API Usage

The API is available at `http://localhost:8000`.

- **Swagger UI docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Ollama-compatible endpoints:**
  - `POST /api/chat` — Chat endpoint (same as Ollama API, but with MCP tool support)
    - **This is the only endpoint where MCP server tools are integrated.** All tool calls are handled and responses are merged transparently for the client.
  - **All other endpoints** (except `/api/chat`, `/health`, and `/version`) are fully proxied to the underlying Ollama server with no modification. You can use your existing Ollama clients and libraries as usual.
- **Bridge-specific endpoints:**
  - `GET /health` — Health check endpoint (not proxied)
  - `GET /version` — Version information and update check

> [!IMPORTANT]
> `/api/chat` is the only endpoint with MCP tool integration. All other endpoints are transparently proxied to Ollama. `/health` and `/version` are specific to the bridge.

This bridge acts as a drop-in proxy for the Ollama API, but with all MCP tools from all connected servers available to every `/api/chat` request. The bridge automatically handles multiple rounds of tool execution until completion, streaming responses in real-time. You can use your existing Ollama clients and libraries with both local and cloud Ollama models, just point them to this bridge instead of your Ollama server.

### Example: Chat
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:0.6b",
    "messages": [
      {
        "role": "system",
        "content": "You are a weather assistant."
      },
      {
        "role": "user",
        "content": "What is the weather like in Paris today?"
      }
    ],
    "think": true,
    "stream": true,
    "options": {
      "temperature": 0.7,
      "top_p": 0.9
    }
  }'
```

> [!TIP]
> Use `/docs` for interactive API exploration and testing.


## Development

### Key Dependencies
- **FastAPI**: Modern web framework for the API
- **Typer**: CLI framework for command-line interface
- **loguru**: Structured logging throughout the application
- **ollama**: Python client for Ollama communication
- **mcp**: Model Context Protocol client library
- **pytest**: Testing framework for API validation

### Testing

The project has two types of tests:

#### Unit Tests (GitHub Actions compatible)
```bash
# Install test dependencies
uv sync --extra test

# Run unit tests (no server required)
uv run pytest tests/test_unit.py -v
```

These tests check:
- Configuration file loading
- Module imports and initialization
- Project structure
- Tool definition formats

#### Integration Tests (require running services)
```bash
# First, start the server in one terminal
ollama-mcp-bridge

# Then in another terminal, run the integration tests
uv run pytest tests/test_api.py -v
```

These tests check:
- API endpoints with real HTTP requests
- End-to-end functionality with Ollama
- Tool calling and response integration

#### Manual Testing
```bash
# Quick manual test with curl (server must be running)
curl -X GET "http://localhost:8000/health"

# Check version information and update status
curl -X GET "http://localhost:8000/version"

curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3:0.6b", "messages": [{"role": "user", "content": "What tools are available?"}]}'
```

> [!NOTE]
> Tests require the server to be running on localhost:8000. Make sure to start the server before running pytest.

## Related Projects

- [**MCP Client for Ollama**](https://github.com/jonigl/mcp-client-for-ollama) - A text-based user interface (TUI) client for interacting with MCP servers using Ollama. Features include multi-server support, dynamic model switching, streaming responses, tool management, human-in-the-loop capabilities, thinking mode, full model parameters configuration, custom system prompt and saved preferences. Built for developers working with local LLMs.

## Inspiration and Credits

This project is based on the basic MCP client from my Medium article: [Build an MCP Client in Minutes: Local AI Agents Just Got Real](https://medium.com/@jonigl/build-an-mcp-client-in-minutes-local-ai-agents-just-got-real-a10e186a560f).

The inspiration to create this simple bridge came from this GitHub issue: [jonigl/mcp-client-for-ollama#22](https://github.com/jonigl/mcp-client-for-ollama/issues/22), suggested by [@nyomen](https://github.com/nyomen).

---

Made with ❤️ by [jonigl](https://github.com/jonigl)
