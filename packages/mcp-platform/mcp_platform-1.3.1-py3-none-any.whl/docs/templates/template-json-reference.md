# Template.json Configuration Reference

**Complete reference for MCP server template configuration with all supported properties, patterns, and best practices.**

## Overview

The `template.json` file is the core configuration that defines how an MCP server template behaves, deploys, and integrates with the MCP Templates platform. It contains metadata, Docker configuration, transport settings, and a comprehensive configuration schema that controls how users interact with your template.

## Basic Structure

```json
{
  "name": "Template Display Name",
  "description": "Description of what this template does",
  "version": "1.0.0",
  "author": "Your Name",
  "category": "General",
  "tags": ["tag1", "tag2"],
  "docker_image": "dataeverything/mcp-your-template",
  "docker_tag": "latest",
  "ports": {},
  "command": [],
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"]
  },
  "config_schema": {
    "type": "object",
    "properties": {},
    "required": []
  },
  "tool_discovery": "dynamic",
  "tool_endpoint": "/tools",
  "has_image": true,
  "origin": "internal"
}
```

## Core Properties

### Basic Metadata

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✅ | Human-readable display name for the template |
| `description` | string | ✅ | Brief description of template functionality |
| `version` | string | ✅ | Semantic version (e.g., "1.0.0") |
| `author` | string | ✅ | Template author or organization |
| `category` | string | ❌ | Category for organization (default: "General") |
| `tags` | array | ❌ | Array of tags for searchability |

**Example:**
```json
{
  "name": "Filesystem MCP Server",
  "description": "Secure local filesystem access with configurable allowed paths",
  "version": "1.0.0",
  "author": "Data Everything",
  "category": "File System",
  "tags": ["filesystem", "files", "security", "local"]
}
```

### Docker Configuration

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `docker_image` | string | ✅ | Docker image name (without tag) |
| `docker_tag` | string | ❌ | Docker image tag (default: "latest") |
| `ports` | object | ❌ | Port mappings `{"container": host}` |
| `command` | array | ❌ | Override container command |
| `has_image` | boolean | ❌ | Whether Docker image exists (default: true) |
| `origin` | string | ❌ | "internal" or "external" (default: "internal") |

**Example:**
```json
{
  "docker_image": "dataeverything/mcp-github",
  "docker_tag": "latest",
  "ports": {
    "8080": 8080
  },
  "command": ["python", "server.py"],
  "has_image": true,
  "origin": "internal"
}
```

### Transport Configuration

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `transport.default` | string | ✅ | Default transport: "stdio", "http", "sse" |
| `transport.supported` | array | ✅ | Array of supported transports |
| `transport.port` | integer | ❌ | Default port for HTTP transports |

**Transport Types:**
- **`stdio`**: Standard input/output for direct CLI interaction
- **`http`**: HTTP REST API for web integration
- **`sse`**: Server-sent events for streaming
- **`streamable-http`**: HTTP with streaming support

**Example:**
```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"],
    "port": 8080
  }
}
```

### Tool Discovery

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `tool_discovery` | string | ❌ | "static", "dynamic", or "hybrid" (default: "dynamic") |
| `tool_endpoint` | string | ❌ | HTTP endpoint for tool discovery (default: "/tools") |
| `tools` | array | ❌ | Static tool definitions (for static discovery) |
| `capabilities` | array | ❌ | Template capabilities description |

**Discovery Types:**
- **`static`**: Tools defined in template.json
- **`dynamic`**: Tools discovered from running container
- **`hybrid`**: Combination of static and dynamic

**Example:**
```json
{
  "tool_discovery": "dynamic",
  "tool_endpoint": "/tools",
  "capabilities": [
    {
      "name": "File Operations",
      "description": "Read, write, and manage files securely",
      "example": "Read configuration files, process documents"
    }
  ]
}
```

## Response Formatting

Templates can provide custom response formatting to improve the display of tool outputs. This allows templates to transform raw tool responses into beautiful, structured presentations.

### Response Formatter Configuration

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `response_formatter` | object | ❌ | Configuration for custom response formatting |
| `response_formatter.enabled` | boolean | ❌ | Enable custom formatting (default: true if formatter exists) |
| `response_formatter.module` | string | ❌ | Python module name (default: "response_formatter") |
| `response_formatter.class` | string | ❌ | Formatter class name (auto-detected if not specified) |
| `response_formatter.tools` | array | ❌ | List of tools to format (default: all tools) |

**Basic Example:**
```json
{
  "response_formatter": {
    "enabled": true,
    "tools": ["list_indices", "search", "get_index"]
  }
}
```

**Advanced Example:**
```json
{
  "response_formatter": {
    "enabled": true,
    "module": "custom_formatter",
    "class": "MyCustomResponseFormatter",
    "tools": ["list_data", "query_results"]
  }
}
```

### Convention-Based Discovery

If no `response_formatter` configuration is provided, the platform will automatically look for:

1. **Module**: `response_formatter.py` in the template directory
2. **Class**: Auto-detected based on template name (e.g., `ElasticsearchResponseFormatter`)

### Creating a Response Formatter

Create a `response_formatter.py` file in your template directory:

```python
from typing import Optional
from rich.console import Console

class YourTemplateResponseFormatter:
    """Custom response formatter for your template."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the formatter."""
        self.console = console or Console()

    def format_tool_response(self, tool_name: str, raw_response: str) -> None:
        """
        Format tool response for display.

        Args:
            tool_name: Name of the tool that was called
            raw_response: Raw response string from the tool
        """
        if tool_name == "your_tool":
            self._format_your_tool(raw_response)
        else:
            self._format_default(raw_response)

    def _format_your_tool(self, response: str) -> None:
        """Format specific tool output."""
        # Custom formatting logic here
        self.console.print(f"Formatted: {response}")

    def _format_default(self, response: str) -> None:
        """Default formatting fallback."""
        self.console.print(response)
```

### Best Practices

- **Clean JSON responses**: Parse JSON and display as structured tables
- **Handle errors gracefully**: Always provide fallback formatting
- **Use Rich library**: Leverage Rich tables, panels, and syntax highlighting
- **Tool-specific logic**: Different tools may need different formatting approaches
- **Performance**: Keep formatting fast, avoid heavy processing

## Conditional Validation (if/then/else, anyOf, oneOf)

Templates can express complex conditional configuration requirements using JSON Schema constructs. MCP supports three common patterns:

- if/then/else
- anyOf
- oneOf

When to use each
- if/then/else: Use when there is a single binary condition that changes which fields are required or constrained. Example: when `oauth_enabled` is false require `trino_password`, otherwise require `oauth_provider`. This is the clearest choice for feature flags or boolean-based branches.
- anyOf: Use when at least one of multiple independent schemas must be satisfied. Useful when there are multiple valid configuration options and they are not mutually exclusive. Example: support either API key auth or OAuth; a config is valid if it matches any option.
- oneOf: Use when exactly one of multiple mutually-exclusive schemas must be satisfied. Use this when options are exclusive and providing multiple at once should be rejected (e.g., you can select exactly one authentication backend).

Examples

1) if/then/else (binary choice)

```json
{
  "config_schema": {
    "properties": {
      "oauth_enabled": { "type": "boolean", "title": "Enable OAuth" },
      "trino_password": { "type": "string", "title": "Trino Password" },
      "oauth_provider": { "type": "string", "title": "OAuth Provider" }
    },
    "required": ["trino_host", "trino_user"],
    "if": { "properties": { "oauth_enabled": { "const": false } } },
    "then": { "required": ["trino_password"] },
    "else": { "required": ["oauth_provider"] }
  }
}
```

2) anyOf (one of many options is sufficient)

```json
{
  "config_schema": {
    "anyOf": [
      { "required": ["api_key"] },
      { "required": ["oauth_provider", "oidc_client_id"] }
    ]
  }
}
```

3) oneOf (exactly one option must match)

```json
{
  "config_schema": {
    "oneOf": [
      { "required": ["basic_user", "basic_password"] },
      { "required": ["oauth_provider", "oidc_client_id"] }
    ]
  }
}
```

Tips and recommendations
- Prefer `if/then/else` when branching is based on a single property (e.g., a boolean). It is explicit and maps well to UI flows.
- Use `anyOf` for flexible choices where multiple options may be valid concurrently.
- Use `oneOf` to enforce mutual exclusion between configuration options.
- Provide `title` and `description` for properties referenced in conditional blocks to improve generated suggestions and UI text.

Documentation and validation
- The MCP `ConfigProcessor` supports `anyOf`, `oneOf`, and top-level `if/then/else` constructs in `config_schema`. When conditional validation fails, MCP will report missing fields and provide suggestions where possible.
- If you need more advanced validation (nested combinations), prefer expressing them clearly and add unit tests for your template to avoid surprises.

## Configuration Schema

The `config_schema` defines how users configure your template. It follows JSON Schema specification with additional MCP-specific properties.

### Basic Schema Structure

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "property_name": {
        "type": "string|integer|boolean|array|object",
        "title": "Display Name",
        "description": "Human-readable description",
        "default": "default_value",
        "env_mapping": "ENVIRONMENT_VARIABLE",
        "sensitive": true|false,
        "volume_mount": true|false,
        "command_arg": true|false,
        "enum": ["option1", "option2"]
      }
    },
    "required": ["required_property1", "required_property2"]
  }
}
```

### Configuration Property Types

#### String Properties

```json
{
  "api_key": {
    "type": "string",
    "title": "API Key",
    "description": "Authentication key for the service",
    "env_mapping": "API_KEY",
    "sensitive": true
  },
  "log_level": {
    "type": "string",
    "title": "Log Level",
    "description": "Logging verbosity",
    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
    "default": "INFO",
    "env_mapping": "LOG_LEVEL"
  }
}
```

#### Integer/Number Properties

```json
{
  "timeout": {
    "type": "integer",
    "title": "Request Timeout",
    "description": "HTTP request timeout in seconds",
    "default": 30,
    "env_mapping": "REQUEST_TIMEOUT"
  },
  "rate_limit": {
    "type": "number",
    "title": "Rate Limit",
    "description": "Requests per second limit",
    "default": 10.5,
    "env_mapping": "RATE_LIMIT"
  }
}
```

#### Boolean Properties

```json
{
  "enable_cache": {
    "type": "boolean",
    "title": "Enable Caching",
    "description": "Enable response caching for performance",
    "default": true,
    "env_mapping": "ENABLE_CACHE"
  }
}
```

#### Array Properties

```json
{
  "allowed_domains": {
    "type": "array",
    "title": "Allowed Domains",
    "description": "List of domains to allow access",
    "items": {
      "type": "string"
    },
    "default": ["localhost"],
    "env_mapping": "ALLOWED_DOMAINS",
    "env_separator": ","
  }
}
```

### Advanced MCP Properties

#### Volume Mount Configuration

Use `volume_mount: true` to automatically create Docker volume mounts from configuration values:

```json
{
  "data_directory": {
    "type": "string",
    "title": "Data Directory",
    "description": "Local directory for data storage",
    "default": "/tmp/data",
    "env_mapping": "DATA_DIRECTORY",
    "volume_mount": true
  },
  "allowed_paths": {
    "type": "string",
    "title": "Allowed File Paths",
    "description": "Space-separated list of allowed paths",
    "env_mapping": "ALLOWED_PATHS",
    "volume_mount": true,
    "command_arg": true
  }
}
```

**How it works:**
- Input: `"allowed_paths": "/home/user/docs /tmp/workspace"`
- Creates volumes: `-v "/home/user/docs:/data/docs:rw" -v "/tmp/workspace:/data/workspace:rw"`
- Sets environment: `ALLOWED_PATHS="/data/docs /data/workspace"`

#### Command Argument Injection

Use `command_arg: true` to inject configuration values as command-line arguments:

```json
{
  "config_file": {
    "type": "string",
    "title": "Config File Path",
    "description": "Path to configuration file",
    "env_mapping": "CONFIG_FILE",
    "command_arg": true
  }
}
```

**How it works:**
- Input: `"config_file": "/etc/app/config.json"`
- Adds to container command: `--config-file=/etc/app/config.json`

#### Sensitive Values

Mark sensitive configuration as such to enable masking in logs and UI:

```json
{
  "api_secret": {
    "type": "string",
    "title": "API Secret",
    "description": "Secret key for API authentication",
    "env_mapping": "API_SECRET",
    "sensitive": true
  }
}
```

## Complete Examples

### Stdio Template (Filesystem)

```json
{
  "name": "Filesystem",
  "description": "Local filesystem access with configurable allowed paths",
  "version": "1.0.0",
  "author": "Data Everything",
  "category": "File System",
  "tags": ["filesystem", "files", "local"],
  "docker_image": "dataeverything/mcp-filesystem",
  "docker_tag": "latest",
  "ports": {},
  "command": [],
  "transport": {
    "default": "stdio",
    "supported": ["stdio"]
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "allowed_dirs": {
        "type": "string",
        "title": "Allowed Directories",
        "description": "Space-separated allowed directories for file access",
        "env_mapping": "ALLOWED_DIRS",
        "volume_mount": true,
        "command_arg": true
      },
      "log_level": {
        "type": "string",
        "title": "Log Level",
        "description": "Logging verbosity level",
        "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "default": "INFO",
        "env_mapping": "LOG_LEVEL"
      }
    },
    "required": ["allowed_dirs"]
  },
  "tool_discovery": "dynamic",
  "tool_endpoint": "/tools",
  "has_image": true,
  "origin": "internal"
}
```

### HTTP Template (API Server)

```json
{
  "name": "Weather API Server",
  "description": "Weather data integration MCP server",
  "version": "1.0.0",
  "author": "Weather Corp",
  "category": "API Integration",
  "tags": ["weather", "api", "forecast"],
  "docker_image": "weathercorp/mcp-weather",
  "docker_tag": "latest",
  "ports": {
    "8080": 8080
  },
  "command": ["python", "server.py"],
  "transport": {
    "default": "http",
    "supported": ["http", "stdio"],
    "port": 8080
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "title": "Weather API Key",
        "description": "API key from weather service provider",
        "env_mapping": "WEATHER_API_KEY",
        "sensitive": true
      },
      "api_base_url": {
        "type": "string",
        "title": "API Base URL",
        "description": "Base URL for weather API",
        "default": "https://api.openweathermap.org",
        "env_mapping": "WEATHER_API_URL"
      },
      "cache_duration": {
        "type": "integer",
        "title": "Cache Duration",
        "description": "Cache duration in seconds",
        "default": 300,
        "env_mapping": "CACHE_DURATION"
      },
      "enable_forecasts": {
        "type": "boolean",
        "title": "Enable Forecasts",
        "description": "Enable extended weather forecasts",
        "default": true,
        "env_mapping": "ENABLE_FORECASTS"
      },
      "supported_units": {
        "type": "array",
        "title": "Supported Units",
        "description": "Supported temperature units",
        "items": {
          "type": "string",
          "enum": ["celsius", "fahrenheit", "kelvin"]
        },
        "default": ["celsius", "fahrenheit"],
        "env_mapping": "SUPPORTED_UNITS",
        "env_separator": ","
      }
    },
    "required": ["api_key"]
  },
  "capabilities": [
    {
      "name": "Current Weather",
      "description": "Get current weather conditions",
      "example": "Get temperature, humidity, wind speed for any location"
    },
    {
      "name": "Weather Forecasts",
      "description": "Get weather forecasts up to 7 days",
      "example": "Get daily/hourly forecasts with detailed conditions"
    }
  ],
  "tool_discovery": "dynamic",
  "tool_endpoint": "/tools",
  "has_image": true,
  "origin": "external"
}
```

## Configuration Best Practices

### 1. Required vs Optional Properties

**Required Properties** - Use for essential configuration:
```json
{
  "required": ["api_key", "base_url"]
}
```

**Optional with Defaults** - Provide sensible defaults:
```json
{
  "log_level": {
    "type": "string",
    "default": "INFO",
    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
  }
}
```

### 2. Environment Variable Mapping

Follow consistent naming conventions:
```json
{
  "service_url": {
    "env_mapping": "SERVICE_URL"  // Clear, uppercase
  },
  "api_timeout": {
    "env_mapping": "API_TIMEOUT"  // Consistent prefix
  }
}
```

### 3. Volume Mount Patterns

**Single Directory:**
```json
{
  "data_dir": {
    "type": "string",
    "volume_mount": true,
    "default": "/tmp/data"
  }
}
```

**Multiple Paths:**
```json
{
  "allowed_paths": {
    "type": "string",
    "description": "Space-separated paths",
    "volume_mount": true,
    "command_arg": true
  }
}
```

### 4. Sensitive Data Handling

Always mark sensitive properties:
```json
{
  "api_key": {
    "type": "string",
    "sensitive": true,  // Masks in logs/UI
    "env_mapping": "API_KEY"
  }
}
```

### 5. Type Safety

Use enums for restricted values:
```json
{
  "transport_mode": {
    "type": "string",
    "enum": ["http", "grpc", "websocket"],
    "default": "http"
  }
}
```

## Validation and Testing

### Schema Validation

The platform automatically validates:
- JSON Schema compliance
- Required property presence
- Type correctness
- Enum value validity

### Testing Your Template

```bash
# Validate template.json
mcpp validate templates/my-template/template.json

# Test configuration processing
mcpp config my-template

# Test deployment
mcpp deploy my-template --config-file test-config.json
```

## Migration Guide

### Updating Existing Templates

When adding new MCP-specific properties to existing templates:

1. **Add volume_mount properties:**
```json
{
  "existing_path_config": {
    "type": "string",
    "env_mapping": "EXISTING_PATH",
    "volume_mount": true  // Add this
  }
}
```

2. **Add command_arg properties:**
```json
{
  "config_file_path": {
    "type": "string",
    "env_mapping": "CONFIG_FILE",
    "command_arg": true  // Add this
  }
}
```

3. **Update transport configuration:**
```json
{
  "transport": {
    "default": "stdio",
    "supported": ["stdio", "http"],  // Add HTTP if needed
    "port": 8080  // Add if HTTP supported
  }
}
```

### Backward Compatibility

The platform maintains backward compatibility with templates missing:
- `volume_mount` properties (defaults to false)
- `command_arg` properties (defaults to false)
- `sensitive` properties (defaults to false)
- Modern transport configuration (falls back to stdio)

## Next Steps

- [Creating Custom Templates](creating.md) - Full template creation guide
- [Template Testing](testing.md) - Testing strategies and patterns
- [Template Development](development.md) - Advanced development topics
