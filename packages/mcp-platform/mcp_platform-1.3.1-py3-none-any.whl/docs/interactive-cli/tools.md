# `tools` Command

List available tools for a template.

## Functionality
- Lists all tools for the specified template, with details and parameters.
- Can show configuration schema and usage examples.
- Supports server-side tool discovery and static fallback.
- Server does not need to be deployed for tool discovery.

## Options
- `--force-server`: Force server-side tool discovery (MCP probe only, no static fallback).
- `--help`: Show detailed help for the template and its tools.

## Configuration
- No configuration required to list tools.
- For `--help`, template must be available.

## Example
```
tools my_template
```
```
tools my_template --help
```
```
tools my_template --force-server
```

## When and How to Run
- Use to see what tools are available for a given template before calling them.
- Run after deploying or selecting a template.

## Example Output

```
mcpp> tools demo
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 🔧 Tool Discovery ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Discovering Tools for Template: demo                                                                                                                                                                                                                                                                                                                                                                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
Discovery method: template_json
Source: template.json
Last updated: 2025-08-06 09:46:16
                                                             Available Tools (3 found)
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Tool Name            ┃ Description                                        ┃ Parameters                                         ┃ Category        ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ say_hello            │ Generate a personalized greeting message           │ 1 params (name)                                    │ general         │
│ get_server_info      │ Get information about the demo server              │ 0 params ()                                        │ general         │
│ echo_message         │ Echo back a message with server identification     │ 1 params (message)                                 │ general         │
└──────────────────────┴────────────────────────────────────────────────────┴────────────────────────────────────────────────────┴─────────────────┘
Source: template_json (template.json)
```
- The table shows the tool name, description, parameters, and category.
- Parameters are listed with their names if available, or as "Schema defined" if using an input schema.
- Categories help organize tools by their functionality.
- If `--help` is used, it provides detailed information about each tool's configuration and usage examples.
- If `--force-server` is used, it will only show tools discovered from the server, skipping any static fallback.
- If no tools are available, it will indicate that no tools were found for the specified template.
