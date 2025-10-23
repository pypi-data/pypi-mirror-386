"""
Integration tests for Github template.
"""

# Import MCP testing utilities
import sys

import pytest
import pytest_asyncio

# Import MCP testing utilities
from mcp_platform.utils import TEMPLATES_DIR, TESTS_DIR

sys.path.insert(0, str(TESTS_DIR))

from mcp_test_utils import MCPTestClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestGithubIntegration:
    """Integration tests for Github template."""

    @pytest_asyncio.fixture
    async def mcp_client(self):
        """Create MCP test client."""
        template_dir = TEMPLATES_DIR / "github"
        client = MCPTestClient(template_dir / "server.py")
        await client.start()
        yield client
        await client.stop()

    async def test_server_connection(self, mcp_client):
        """Test MCP server connection."""
        tools = await mcp_client.list_tools()
        assert len(tools) >= 0  # Server should be accessible

    async def test_example_integration(self, mcp_client):
        """Test example integration."""
        result = await mcp_client.call_tool("example", {})
        assert result is not None
        # TODO: Add specific assertions for example
