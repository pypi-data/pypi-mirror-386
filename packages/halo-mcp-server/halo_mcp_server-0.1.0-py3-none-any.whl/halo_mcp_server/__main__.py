"""Main entry point for Halo MCP Server."""

import asyncio
import sys

from loguru import logger

from halo_mcp_server.config import settings
from halo_mcp_server.server import run_server
from halo_mcp_server.utils.logger import setup_logger


async def main() -> None:
    """Main function."""
    try:
        # Setup logger
        setup_logger(settings.mcp_log_level)

        logger.info("=" * 60)
        logger.info("Halo MCP Server Starting...")
        logger.info(f"Version: 0.1.0")
        logger.info(f"Halo Server: {settings.halo_base_url or 'Not configured'}")
        logger.info(f"Log Level: {settings.mcp_log_level}")
        logger.info("=" * 60)

        # Check base URL configuration
        if not settings.halo_base_url:
            logger.error("HALO_BASE_URL is not configured!")
            logger.error("Please set HALO_BASE_URL as environment variable")
            logger.error("For Claude Desktop, configure it in the MCP JSON configuration file")
            logger.error("For standalone use, you can set it in a .env file or as environment variable")
            sys.exit(1)

        # Check authentication
        if not settings.has_valid_auth:
            logger.error("No authentication configured!")
            logger.error("Please set HALO_TOKEN or HALO_USERNAME/HALO_PASSWORD as environment variables")
            logger.error("For Claude Desktop, configure them in the MCP JSON configuration file")
            logger.error("For standalone use, you can set them in a .env file or as environment variables")
            sys.exit(1)

        # Run MCP server
        await run_server()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
