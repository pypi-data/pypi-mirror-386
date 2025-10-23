"""
Main entry point for running the Cerevox MCP server.

Run with: python -m cerevox_mcp_server
"""

import asyncio
from . import main

if __name__ == "__main__":
    asyncio.run(main())
