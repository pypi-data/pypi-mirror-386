"""AgentRun Code Interpreter MCP Server package."""

__all__ = ['main']


def main():
    """Main entry point for the package."""
    import asyncio
    from .main import main as server_main
    asyncio.run(server_main())
