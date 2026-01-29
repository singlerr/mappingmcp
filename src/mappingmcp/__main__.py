"""Entry point for running the MCP server."""

import os
from mappingmcp.server import mcp

if __name__ == "__main__":
    # Get transport settings from environment variables
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8080"))
    
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    elif transport in ("streamable-http", "http"):
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        print(f"Unknown transport: {transport}")
        print("Supported transports: stdio, sse, streamable-http (or http)")
        exit(1)
