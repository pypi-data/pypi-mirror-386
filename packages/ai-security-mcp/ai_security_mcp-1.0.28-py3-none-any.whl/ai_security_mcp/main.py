#!/usr/bin/env python3
"""
AI Security MCP Thin Client
Lightweight MCP server that proxies requests to cloud MCP server via HTTP
"""

import asyncio
import httpx
import logging
import os
import sys
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging to stderr (stdio goes to stdout for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Cloud MCP server URL
CLOUD_MCP_URL = os.getenv(
    'AI_SECURITY_MCP_URL',
    'https://ai-security-mcp-fastmcp-production-722116092626.us-central1.run.app'
)

# User's API key from environment
API_KEY = os.getenv('AI_SECURITY_API_KEY')

# HTTP client for cloud API calls
http_client: Optional[httpx.AsyncClient] = None


class ScanResult(BaseModel):
    """Security scan result model"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def validate_environment():
    """Validate required environment variables"""
    if not API_KEY:
        logger.error("AI_SECURITY_API_KEY environment variable is required")
        print("\n" + "="*60, file=sys.stderr)
        print("ERROR: API Key Required", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("\nThe AI Security MCP thin client requires an API key.", file=sys.stderr)
        print("\nSteps to get your API key:", file=sys.stderr)
        print("1. Visit: https://app.ai-threat-scanner.com/dashboard/api-keys", file=sys.stderr)
        print("2. Generate a new API key", file=sys.stderr)
        print("3. Set environment variable:", file=sys.stderr)
        print("   export AI_SECURITY_API_KEY=ciso_live_your_key_here", file=sys.stderr)
        print("\nOr configure in Claude Code:", file=sys.stderr)
        print("   Add to .claude/settings.json:", file=sys.stderr)
        print('   "env": {"AI_SECURITY_API_KEY": "ciso_live_your_key_here"}', file=sys.stderr)
        print("\n" + "="*60, file=sys.stderr)
        sys.exit(1)

    logger.info("Environment validation passed")
    logger.info(f"Using cloud MCP server: {CLOUD_MCP_URL}")
    logger.info(f"API key configured: {API_KEY[:15]}...")


async def call_cloud_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a tool on the cloud MCP server via HTTP

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool result from cloud server
    """
    global http_client

    if http_client is None:
        http_client = httpx.AsyncClient(timeout=60.0)

    try:
        # Call cloud MCP server's custom HTTP endpoint (no session required)
        response = await http_client.post(
            f"{CLOUD_MCP_URL}/api/tools/call",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(f"Cloud MCP error: {result['error']}")

        return result.get("result", {})

    except Exception as e:
        logger.error(f"Failed to call cloud tool {tool_name}: {e}")
        raise


# Initialize FastMCP server
mcp = FastMCP(
    "AI Security Scanner",
    version="1.0.28"
)


@mcp.tool()
async def scan_repository(
    path: str = Field(
        description="File or directory path to scan for security vulnerabilities"
    ),
    format: str = Field(
        default="detailed",
        description="Output format: 'detailed' or 'summary'"
    )
) -> ScanResult:
    """
    Scan repository or file path for AI security vulnerabilities.

    This tool analyzes code for security issues specific to AI/ML systems including:
    - Prompt injection vulnerabilities
    - Insecure deserialization of models
    - Unsafe model loading
    - Credential exposure in model artifacts
    - AI-specific input validation issues

    Args:
        path: File or directory path to scan
        format: Output format - 'detailed' for full report, 'summary' for overview

    Returns:
        ScanResult with vulnerability findings

    Example:
        scan_repository(path="/path/to/code", format="detailed")
    """
    try:
        logger.info(f"Scanning repository: {path}")

        # Call cloud MCP server
        result = await call_cloud_tool(
            "scan_repository",
            {"path": path, "format": format}
        )

        logger.info(f"Scan completed: {path}")

        return ScanResult(
            success=True,
            data=result,
            metadata={"path": path, "format": format}
        )

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return ScanResult(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check health status of the AI Security Scanner service.

    Returns service health information including:
    - Service status (healthy, degraded, unhealthy)
    - Database connectivity
    - Active API keys count
    - Service uptime

    Returns:
        Health status information

    Example:
        health_check()
    """
    try:
        logger.info("Performing health check")

        # Call cloud MCP server
        result = await call_cloud_tool("health_check", {})

        logger.info(f"Health check result: {result.get('status', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def main():
    """Main entry point for the thin client"""
    logger.info("AI Security MCP Thin Client starting...")

    # Validate environment
    validate_environment()

    try:
        # Run FastMCP server over stdio
        logger.info("Starting MCP server over stdio...")
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("Thin client stopped by user")
    except Exception as e:
        logger.error(f"Thin client failed: {str(e)}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup
        if http_client:
            asyncio.run(http_client.aclose())
        logger.info("AI Security MCP Thin Client terminated")


if __name__ == "__main__":
    main()
