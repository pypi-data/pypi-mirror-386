"""
Template discovery module for MCP Platform server templates.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_platform.utils import TEMPLATES_DIR, get_all_template_directories

logger = logging.getLogger(__name__)


# Constants
DEFAULT_DATA_PATH = "/data"
DEFAULT_LOGS_PATH = "/logs"


class TemplateDiscovery:
    """Dynamic template discovery from templates directory."""

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        templates_dirs: Optional[List[Path]] = None,
    ):
        """Initialize template discovery.

        Args:
            templates_dir: Single template directory (for backward compatibility)
            templates_dirs: List of template directories (new functionality)
        """
        if templates_dirs is not None:
            # Use provided list of directories
            self.templates_dirs = templates_dirs
        elif templates_dir is not None:
            # Use single directory (backward compatibility)
            self.templates_dirs = [templates_dir]
        else:
            # Default to all template directories (built-in + custom)
            self.templates_dirs = get_all_template_directories()

        # Keep templates_dir for backward compatibility
        self.templates_dir = (
            self.templates_dirs[0] if self.templates_dirs else TEMPLATES_DIR
        )

    def discover_templates(self) -> Dict[str, Dict[str, Any]]:
        """Discover all valid templates in all template directories."""
        templates = {}

        # Iterate through directories in reverse order so first directory
        # (custom) takes precedence
        for templates_dir in reversed(self.templates_dirs):
            if not templates_dir.exists():
                logger.debug("Templates directory not found: %s", templates_dir)
                continue

            for template_dir in templates_dir.iterdir():
                if not template_dir.is_dir():
                    continue

                template_name = template_dir.name
                template_config = self._load_template_config(template_dir)

                if template_config:
                    # Mark source of template for debugging
                    template_config["source_directory"] = str(templates_dir)
                    templates[template_name] = template_config
                    logger.debug(
                        "Discovered template: %s from %s", template_name, templates_dir
                    )
                else:
                    logger.debug(
                        "Skipped invalid template: %s from %s",
                        template_name,
                        templates_dir,
                    )

        return templates

    def _load_template_config(self, template_dir: Path) -> Optional[Dict[str, Any]]:
        """Load and validate a template configuration."""
        template_json = template_dir / "template.json"

        # Basic validation: must have template.json and Dockerfile
        if not template_json.exists():
            logger.debug("Template %s missing template.json", template_dir.name)
            return None

        try:
            # Load template metadata
            with open(template_json, encoding="utf-8") as f:
                template_data = json.load(f)

            # Generate deployment configuration
            config = self._generate_template_config(template_data, template_dir)

            return config

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.debug("Failed to load template %s: %s", template_dir.name, e)
            return None

    def _generate_template_config(
        self, template_data: Dict[str, Any], template_dir: Path
    ) -> Dict[str, Any]:
        """Generate deployment configuration from template metadata."""

        # Extract basic info
        config = {
            "name": template_data.get("name", template_dir.name.title()),
            "description": template_data.get("description", "MCP server template"),
            "version": template_data.get("version", "latest"),
            "category": template_data.get("category", "general"),
            "tags": template_data.get("tags", []),
        }

        # Docker image configuration
        config["image"] = self._get_docker_image(template_data, template_dir.name)

        # Keep original docker_image field for backward compatibility
        if "docker_image" in template_data:
            config["docker_image"] = template_data["docker_image"]

        # Environment variables from config schema
        config["env_vars"] = self._extract_env_vars(template_data)

        # Volume mounts
        config["volumes"] = self._extract_volumes(template_data)

        # Port mappings
        config["ports"] = self._extract_ports(template_data)

        # Required tokens/secrets
        config.update(self._extract_requirements(template_data))

        # Include the original config schema for CLI usage
        config["config_schema"] = template_data.get("config_schema", {})

        # Include tools information for CLI usage
        config["tools"] = template_data.get("tools", [])

        # Include transport information for CLI usage
        config["transport"] = template_data.get(
            "transport", {"default": "stdio", "supported": ["stdio"]}
        )

        # Include tool discovery method for CLI usage
        config["tool_discovery"] = template_data.get("tool_discovery")

        # Include capabilities for CLI usage
        config["capabilities"] = template_data.get("capabilities", [])

        # Generate MCP client configuration
        config["example_config"] = self._generate_mcp_config(
            template_data, template_dir.name
        )

        return config

    def get_template_config(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific template."""
        # Search in all template directories, first match wins
        # (custom overrides built-in)
        for templates_dir in self.templates_dirs:
            template_dir = templates_dir / template_name
            if template_dir.exists():
                return self._load_template_config(template_dir)
        return None

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get the path to a specific template."""
        # Search in all template directories, first match wins
        # (custom overrides built-in)
        for templates_dir in self.templates_dirs:
            template_dir = templates_dir / template_name
            if template_dir.exists() and template_dir.is_dir():
                return template_dir
        return None

    def _get_docker_image(
        self, template_data: Dict[str, Any], template_name: str
    ) -> str:
        """Get Docker image name for template."""
        if "docker_image" in template_data:
            docker_tag = template_data.get("docker_tag", "latest")
            return f"{template_data['docker_image']}:{docker_tag}"
        else:
            # Fallback to standard naming
            return f"dataeverything/mcp-{template_name}:latest"

    def _extract_env_vars(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract default environment variables from config schema."""
        env_vars = {}

        # Get environment variables from template
        if "environment_variables" in template_data:
            env_vars.update(template_data["environment_variables"])

        # Extract defaults from config schema
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for _, prop_config in properties.items():
            if "default" in prop_config:
                # Map to environment variable if mapping exists
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    default_value = prop_config["default"]
                    if isinstance(default_value, list):
                        separator = prop_config.get("env_separator", ",")
                        env_vars[env_mapping] = separator.join(
                            str(item) for item in default_value
                        )
                    else:
                        env_vars[env_mapping] = str(default_value)

        return env_vars

    def _extract_volumes(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract volume mounts from template configuration."""
        volumes = {
            "~/mcp-data": DEFAULT_DATA_PATH,
            "~/.mcp/logs": DEFAULT_LOGS_PATH,
        }

        # Default volumes
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Look for directory-type configurations
        for prop_name, prop_config in properties.items():
            if (
                prop_config.get("type") == "array"
                and "directories" in prop_name.lower()
            ):
                # This is likely a directory configuration
                default_dirs = prop_config.get("default", [])
                for i, directory in enumerate(default_dirs):
                    host_path = (
                        f"~/mcp-data/{prop_name}_{i}"
                        if len(default_dirs) > 1
                        else "~/mcp-data"
                    )
                    volumes[host_path] = directory

        return volumes

    def _extract_ports(self, template_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract port mappings from template configuration."""
        ports = {}

        # Check if template specifies ports
        if "ports" in template_data:
            ports.update(template_data["ports"])

        # Most MCP servers don't need exposed ports by default
        return ports

    def _extract_requirements(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements like tokens from template configuration."""
        requirements = {}

        # Check config schema for required tokens
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            if "token" in prop_name.lower() or "key" in prop_name.lower():
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    requirements["requires_token"] = env_mapping
                    break

        return requirements

    def _generate_mcp_config(
        self, template_data: Dict[str, Any], template_name: str
    ) -> str:
        """Generate MCP client configuration JSON."""
        config = {
            "servers": {
                f"{template_name}-server": {
                    "command": "docker",
                    "args": [
                        "exec",
                        "-i",
                        f"mcp-{template_name}",
                        "python",
                        "server.py",
                    ],
                }
            }
        }

        # Add environment variables if template requires tokens
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        env_vars = {}
        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            if "token" in prop_name.lower() or "key" in prop_name.lower():
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    env_vars[env_mapping] = (
                        f"your-{prop_name.lower().replace('_', '-')}-here"
                    )

        if env_vars:
            config["servers"][f"{template_name}-server"]["env"] = env_vars

        return json.dumps(config, indent=2)

    def validate_template_config(self, template_config: Dict[str, Any]) -> bool:
        """Validate template configuration."""
        required_fields = ["name", "description", "image"]

        for field in required_fields:
            if field not in template_config:
                logger.error("Missing required field: %s", field)
                return False

        # Validate image format
        if "image" in template_config:
            image = template_config["image"]
            if not isinstance(image, str) or ":" not in image:
                logger.error("Invalid image format: %s", image)
                return False

        return True

    def is_template(self, name: str) -> bool:
        """
        Check if a given name corresponds to a valid template.
        """

        templates = self.discover_templates()
        return name in templates
