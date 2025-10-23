"""
MCP Platform Deployment Tool

A unified deployment system that provides:
- Rich CLI interface for standalone users
- Backend abstraction for different deployment targets
- Dynamic template discovery and configuration management
- Zero-configuration deployment experience

The system follows a layered architecture:
1. CLI Layer: Rich interface for user interaction
2. Management Layer: DeploymentManager orchestrates operations
3. Backend Layer: Pluggable deployment services (Docker, Kubernetes, etc.)
4. Discovery Layer: Dynamic template detection and configuration

Key Features:
- Template-driven configuration (no hardcoded template logic)
- Configurable image pulling (supports local development)
- Generic deployment utilities (reusable across templates)
- Comprehensive error handling and logging
"""

import logging

# Import version
from mcp_platform.__version__ import __version__
from mcp_platform.backends.docker import DockerDeploymentService
from mcp_platform.cli import app
from mcp_platform.client import MCPClient
from mcp_platform.core import DeploymentManager as CommonDeploymentManager
from mcp_platform.core import TemplateManager, ToolManager
from mcp_platform.core.deployment_manager import DeploymentManager
from mcp_platform.template.utils.creation import TemplateCreator
from mcp_platform.template.utils.discovery import TemplateDiscovery

# Export the classes for external use (CI compatibility)
__all__ = [
    "TemplateDiscovery",
    "DockerDeploymentService",
    "DeploymentManager",
    "TemplateCreator",
    "MCPClient",
    "TemplateManager",
    "CommonDeploymentManager",
    "ToolManager",
    # "ServerRegistry",
    # "LoadBalancer",
    # "HealthChecker",
    "__version__",
]

# Constants
DEFAULT_CONFIG_PATH = "/config"
CUSTOM_NAME_HELP = "Custom container name"

# Console and logger initialization moved to functions to avoid import issues
console = None
logger = logging.getLogger(__name__)
enhanced_cli = None


def main():
    """
    Main entry point for the MCP deployer CLI.
    Uses Typer-based CLI with autocomplete and enhanced features.
    """

    app()


if __name__ == "__main__":
    main()
