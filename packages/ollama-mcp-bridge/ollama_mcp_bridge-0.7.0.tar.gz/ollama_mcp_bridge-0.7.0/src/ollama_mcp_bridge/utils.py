"""Utility functions for ollama-mcp-bridge"""
import os
import json
import re
import httpx
import typer
from typer import BadParameter
from loguru import logger
from packaging import version as pkg_version
from fastapi.middleware.cors import CORSMiddleware
import sys


def configure_cors(app):
    """Configure CORS middleware for the FastAPI app."""

    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    cors_origins = [origin.strip() for origin in cors_origins]

    # Don't log CORS config if the user is checking the version
    is_version_check = any('--version' in arg for arg in sys.argv)

    if not is_version_check:
        if cors_origins == ["*"]:
            logger.warning("CORS is configured to allow ALL origins (*). This is not recommended for production.")
        else:
            logger.info(f"CORS configured to allow origins: {cors_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def check_ollama_health(ollama_url: str, timeout: int = 3) -> bool:
    """Check if Ollama server is running and accessible (sync version for CLI)."""
    try:
        resp = httpx.get(f"{ollama_url}/api/tags", timeout=timeout)
        if resp.status_code == 200:
            logger.success("✓ Ollama server is accessible")
            return True
        logger.error(f"Ollama server not accessible at {ollama_url}")
        return False
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

async def check_ollama_health_async(ollama_url: str, timeout: int = 3) -> bool:
    """Check if Ollama server is running and accessible (async version for FastAPI)."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ollama_url}/api/tags", timeout=timeout)
            if resp.status_code == 200:
                return True
            logger.error(f"Ollama server not accessible at {ollama_url}")
            return False
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPError) as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

async def iter_ndjson_chunks(chunk_iterator):
    """Async generator that yields parsed JSON objects from NDJSON (newline-delimited JSON) byte chunks."""
    buffer = b""
    async for chunk in chunk_iterator:
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.debug(f"Error parsing NDJSON line: {e}")
    # Handle any trailing data
    if buffer.strip():
        try:
            yield json.loads(buffer)
        except json.JSONDecodeError as e:
            logger.debug(f"Error parsing trailing NDJSON: {e}")

def validate_cli_inputs(config: str, host: str, port: int, ollama_url: str, max_tool_rounds: int = None, system_prompt: str = None):
    """Validate CLI inputs for config file, host, port, ollama_url, max_tool_rounds and system_prompt.

    Args:
        system_prompt: optional system prompt string; if provided, must be a non-empty string and not excessively long.
    """
    # Validate config file exists
    if not os.path.isfile(config):
        raise BadParameter(f"Config file not found: {config}")

    # Validate port
    if not 1 <= port <= 65535:
        raise BadParameter(f"Port must be between 1 and 65535, got {port}")

    # Validate host (basic check)
    if not isinstance(host, str) or not host:
        raise BadParameter("Host must be a non-empty string")

    # Validate URL (basic check)
    url_pattern = re.compile(r"^https?://[\w\.-]+(:\d+)?")
    if not url_pattern.match(ollama_url):
        raise BadParameter(f"Invalid Ollama URL: {ollama_url}")

    # Validate max_tool_rounds
    if max_tool_rounds is not None and max_tool_rounds < 1:
        raise BadParameter(f"max_tool_rounds must be at least 1, got {max_tool_rounds}")

    # Validate system_prompt (if provided)
    if system_prompt is not None:
        if not isinstance(system_prompt, str):
            raise BadParameter("system_prompt must be a string")
        # Reject empty or whitespace-only prompts
        if not system_prompt.strip():
            raise BadParameter("system_prompt must be a non-empty string")
        # Limit length to a reasonable maximum to avoid excessively large payloads
        if len(system_prompt) > 10000:
            raise BadParameter("system_prompt is too long (max 10000 characters)")

async def check_for_updates(current_version: str, print_message: bool = False) -> str:
    """
    Check if a newer version of ollama-mcp-bridge is available on PyPI.

    Args:
        current_version: The current version of the package
        print_message: If True, print the update message to stdout instead of logging

    Returns:
        str: The latest version if an update is available, otherwise the current version
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://pypi.org/pypi/ollama-mcp-bridge/json",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("info", {}).get("version", "0.0.0")

                # Compare versions
                current_v = pkg_version.parse(current_version)
                latest_v = pkg_version.parse(latest_version)

                if latest_v > current_v:
                    upgrade_cmd = "pip install --upgrade ollama-mcp-bridge"

                    # Show message based on requested output method
                    update_msg = f"📦 Update available: v{current_version} → v{latest_version}"
                    upgrade_msg = f"To upgrade, run: {upgrade_cmd}"

                    if print_message:
                        typer.echo(typer.style(update_msg, fg=typer.colors.BRIGHT_GREEN, bold=True))
                        typer.echo(typer.style(upgrade_msg, fg=typer.colors.BRIGHT_MAGENTA, bold=True))
                    else:
                        logger.info(update_msg)
                        logger.info(upgrade_msg)

                return latest_version

            return current_version  # Return current version when response doesn't match expected structure
    except (httpx.HTTPError, json.JSONDecodeError, pkg_version.InvalidVersion) as e:
        logger.debug(f"Failed to check for updates: {e}")
        return current_version  # Return current version when check fails
