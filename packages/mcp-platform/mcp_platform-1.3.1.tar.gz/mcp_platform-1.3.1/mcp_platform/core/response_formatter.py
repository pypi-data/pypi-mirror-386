"""
Unified Response Formatter and Visual Design System.

This module combines the ResponseBeautifier functionality from interactive_cli.py
with the multi-backend visual formatting from utils/visual_formatting.py to provide
a comprehensive formatting solution.
"""

import datetime
import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from mcp_platform.backends import VALID_BACKENDS
from mcp_platform.utils import TEMPLATES_DIR

logger = logging.getLogger(__name__)

# Backend visual configuration
BACKEND_COLORS = {
    "docker": "blue",
    "kubernetes": "green",
    "mock": "yellow",
    "unknown": "dim",
}

BACKEND_ICONS = {"docker": "🐳", "kubernetes": "☸️", "mock": "🔧", "unknown": "❓"}

STATUS_COLORS = {
    "running": "green",
    "stopped": "red",
    "starting": "yellow",
    "error": "bright_red",
    "unknown": "dim",
    "pending": "blue",
    "terminating": "orange1",
}

# Constants for tool response formatting
TOOL_RESULT_TITLE = "Tool Result"

console = Console()


def get_backend_color(backend_type: str) -> str:
    """Get color for backend type."""
    return BACKEND_COLORS.get(backend_type, "dim")


def get_backend_icon(backend_type: str) -> str:
    """Get icon for backend type."""
    return BACKEND_ICONS.get(backend_type, "❓")


def get_status_color(status: str) -> str:
    """Get color for deployment status."""
    return STATUS_COLORS.get(status.lower() if status else "unknown", "dim")


def get_backend_indicator(backend_type: str, include_icon: bool = True) -> str:
    """
    Get visual indicator for backend type.

    Args:
        backend_type: Backend type string
        include_icon: Whether to include emoji icon

    Returns:
        Formatted backend indicator string
    """
    icon = get_backend_icon(backend_type) if include_icon else ""
    color = get_backend_color(backend_type)
    name = backend_type.upper()

    if include_icon:
        return f"[{color}] {icon}  {name.strip()}[/]"
    else:
        return f"[{color}] {name}[/]"


def format_timestamp(timestamp: Union[str, datetime.datetime, None]) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Timestamp to format

    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"

    if isinstance(timestamp, str):
        try:
            # Try parsing ISO format
            dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return timestamp[:19] if len(timestamp) > 19 else timestamp
    elif isinstance(timestamp, datetime.datetime):
        dt = timestamp
    else:
        return str(timestamp)

    # Format as relative time if recent, otherwise absolute
    now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
    delta = now - dt

    if delta.days == 0:
        if delta.seconds < 60:
            return "just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}m ago"
        else:
            return f"{delta.seconds // 3600}h ago"
    elif delta.days == 1:
        return "yesterday"
    elif delta.days < 7:
        return f"{delta.days}d ago"
    else:
        return dt.strftime("%Y-%m-%d")


def format_deployment_summary(deployments: List[Dict[str, Any]]) -> str:
    """
    Create a summary string for a list of deployments.

    Args:
        deployments: List of deployment dictionaries

    Returns:
        Summary string
    """
    if not deployments:
        return "No deployments"

    # Count by status
    status_counts = {}
    backend_counts = {}

    for deployment in deployments:
        status = deployment.get("status", "unknown")
        backend = deployment.get("backend_type", "unknown")

        status_counts[status] = status_counts.get(status, 0) + 1
        backend_counts[backend] = backend_counts.get(backend, 0) + 1

    # Build summary
    total = len(deployments)
    summary_parts = [f"{total} total"]

    # Add status breakdown if multiple statuses
    if len(status_counts) > 1:
        running = status_counts.get("running", 0)
        if running > 0:
            summary_parts.append(f"{running} running")

    # Add backend breakdown if multiple backends
    if len(backend_counts) > 1:
        backend_parts = []
        for backend, count in backend_counts.items():
            backend_parts.append(f"{count} {backend}")
        summary_parts.append(f"({', '.join(backend_parts)})")

    return ", ".join(summary_parts)


class ResponseFormatter:
    """Unified response formatter combining MCP response formatting with multi-backend visual formatting."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the response formatter.

        Args:
            verbose: Whether to enable verbose output for debugging
        """
        self.console = Console()
        self.verbose = verbose
        # Default maximum number of rows/items to display in tables/lists
        # Increase from previous small defaults so UI shows more rows by default
        self.max_display_rows = 100

    def _is_actual_error(self, stderr_text: str) -> bool:
        """Check if stderr contains actual errors vs informational messages."""
        if not stderr_text:
            return False

        stderr_lower = stderr_text.lower().strip()

        # These are actual error indicators
        error_indicators = [
            "error:",
            "exception:",
            "traceback",
            "failed:",
            "fatal:",
            "cannot",
            "unable to",
            "permission denied",
            "not found",
            "invalid",
            "syntax error",
            "connection refused",
            "timeout",
        ]

        # These are informational messages that should not be treated as errors
        info_indicators = [
            "running on stdio",
            "server started",
            "listening on",
            "connected to",
            "initialized",
            "ready",
            "starting",
            "loading",
            "loaded",
            "using",
            "found",
        ]

        # Check for actual errors first
        for indicator in error_indicators:
            if indicator in stderr_lower:
                return True

        # If it contains info indicators, it's likely not an error
        for indicator in info_indicators:
            if indicator in stderr_lower:
                return False

        # If stderr is very short and doesn't contain error words, likely not an error
        if len(stderr_text.strip()) < 100 and not any(
            word in stderr_lower for word in ["error", "fail", "exception"]
        ):
            return False

        # Default to showing it if we're unsure
        return True

    def _analyze_data_types(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure and return metadata about its composition."""
        ignore_keys = [
            "success",
            "error",
            "isError",
            "isSuccess",
            "is_erorr",
            "is_success",
        ]
        analysis = {
            "primary_type": type(data).__name__,
            "is_homogeneous": True,
            "element_types": {},
            "structure_hints": [],
            "complexity": "simple",
            "best_display": "raw",
        }
        if isinstance(data, dict):
            for ikey in ignore_keys:
                data.pop(ikey, None)

            analysis["size"] = len(data)
            analysis["element_types"] = {k: type(v).__name__ for k, v in data.items()}

            # Analyze value types for homogeneity
            value_types = set(type(v).__name__ for v in data.values())
            analysis["is_homogeneous"] = len(value_types) == 1
            analysis["value_types"] = list(value_types)

            # Check for common data service response patterns (BigQuery, databases, APIs)
            if self._is_data_service_response(data):
                analysis["complexity"] = "data_service"
                analysis["best_display"] = "data_service"
                analysis["structure_hints"].append("data_service_response")
            # Determine complexity and structure hints
            elif len(data) <= 6 and all(
                isinstance(v, (str, int, float, bool, type(None)))
                for v in data.values()
            ):
                analysis["complexity"] = "simple"
                analysis["best_display"] = "key_value"
                analysis["structure_hints"].append("simple_mapping")
            elif self._is_tabular_dict(data):
                analysis["complexity"] = "tabular"
                analysis["best_display"] = "table"
                analysis["structure_hints"].append("column_oriented")
            elif any(isinstance(v, (list, dict)) for v in data.values()):
                analysis["complexity"] = "nested"
                analysis["best_display"] = "tree" if len(data) <= 10 else "json"
                analysis["structure_hints"].append("hierarchical")
            else:
                analysis["complexity"] = "medium"
                analysis["best_display"] = "key_value" if len(data) <= 15 else "json"

        elif isinstance(data, list):
            analysis["size"] = len(data)
            if data:
                element_types = [type(item).__name__ for item in data]
                analysis["element_types"] = dict(
                    zip(range(len(element_types)), element_types)
                )
                analysis["is_homogeneous"] = len(set(element_types)) == 1
                analysis["item_type"] = (
                    element_types[0] if analysis["is_homogeneous"] else "mixed"
                )

                if analysis["is_homogeneous"]:
                    if isinstance(data[0], dict) and self._has_consistent_keys(data):
                        analysis["complexity"] = "tabular"
                        analysis["best_display"] = "table"
                        analysis["structure_hints"].append("record_list")
                    elif isinstance(data[0], (str, int, float)):
                        analysis["complexity"] = "simple"
                        analysis["best_display"] = "list"
                        analysis["structure_hints"].append("value_list")
                    else:
                        analysis["complexity"] = "nested"
                        analysis["best_display"] = "json"
                        analysis["structure_hints"].append("complex_list")
                else:
                    analysis["complexity"] = "heterogeneous"
                    analysis["best_display"] = "json"
                    analysis["structure_hints"].append("mixed_types")
            else:
                analysis["best_display"] = "empty"

        elif isinstance(data, str):
            try:
                parsed = json.loads(data)
                nested_analysis = self._analyze_data_types(parsed)
                analysis.update(nested_analysis)
                analysis["structure_hints"].append("json_string")
            except json.JSONDecodeError:
                analysis["best_display"] = "text"
                analysis["structure_hints"].append("plain_text")
        else:
            analysis["best_display"] = "simple"

        return analysis

    def _detect_data_structure(self, data: Any) -> str:
        """Detect the type of data structure to apply appropriate formatting."""
        analysis = self._analyze_data_types(data)
        return analysis["best_display"]

    def _is_tabular_dict(self, data: dict) -> bool:
        """Check if dictionary contains tabular data."""
        # Look for patterns like {key1: [values], key2: [values]}
        if len(data) >= 2:
            values = list(data.values())
            if all(isinstance(v, list) and len(v) > 0 for v in values):
                # Check if all lists have same length
                lengths = [len(v) for v in values]
                return len(set(lengths)) == 1
        return False

    def _is_data_service_response(self, data: dict) -> bool:
        """
        Check if dictionary contains data service response patterns like BigQuery, databases, etc.

        Common patterns:
        - {datasets: [...], total_count: n, message: "..."}
        - {rows: [...], count: n, status: "..."}
        - {records: [...], total: n}
        - {results: [...], meta: {...}}
        """
        # Common list keys that contain tabular data
        list_keys = [
            "datasets",
            "tables",
            "rows",
            "records",
            "results",
            "data",
            "items",
            "entries",
        ]

        # Check if we have one of these list keys with data
        for list_key in list_keys:
            if (
                list_key in data
                and isinstance(data[list_key], list)
                and len(data[list_key]) > 0
            ):

                # Check if the list contains dict objects (records)
                first_item = data[list_key][0]
                if isinstance(first_item, dict):
                    # Check if it has consistent keys (tabular structure)
                    if self._has_consistent_keys(
                        data[list_key][:5]
                    ):  # Check first 5 items
                        # Additional check: ensure there are metadata fields alongside the list
                        metadata_keys = set(data.keys()) - {list_key}
                        metadata_values = [data[k] for k in metadata_keys]
                        # Should have simple metadata fields (not deeply nested)
                        if metadata_values and all(
                            isinstance(v, (str, int, float, bool, type(None)))
                            for v in metadata_values
                        ):
                            return True

        return False

    def _has_consistent_keys(self, data: List[dict]) -> bool:
        """Check if list of dicts has consistent keys for table display."""
        if not data or not isinstance(data[0], dict):
            return False

        first_keys = set(data[0].keys())
        return all(
            set(item.keys()) == first_keys for item in data[:5]
        )  # Check first 5 items

    def _create_key_value_table(self, data: dict, title: str = "Data") -> Table:
        """Create a key-value table for simple dictionaries with intelligent formatting."""
        self._analyze_data_types(data)

        table = Table(
            title=f"{title} ({len(data)} properties)",
            show_header=True,
            header_style="cyan",
        )
        table.add_column("Property", style="cyan", width=25)
        table.add_column("Value", style="white", width=55)
        table.add_column("Type", style="yellow", width=10)

        for key, value in data.items():
            value_type = type(value).__name__

            # Format value based on type with intelligent truncation
            if isinstance(value, (dict, list)):
                if isinstance(value, dict):
                    size_info = (
                        f" ({len(value)} keys)" if len(value) > 0 else " (empty)"
                    )
                    preview = (
                        "{"
                        + ", ".join(f"{k}: ..." for k in list(value.keys())[:3])
                        + "}"
                    )
                    if len(value) > 3:
                        preview += "..."
                    preview += size_info
                else:  # list
                    size_info = (
                        f" ({len(value)} items)" if len(value) > 0 else " (empty)"
                    )
                    if len(value) > 0:
                        preview = (
                            "["
                            + ", ".join(
                                str(item)[:10] + ("..." if len(str(item)) > 10 else "")
                                for item in value[:3]
                            )
                            + "]"
                        )
                        if len(value) > 3:
                            preview += "..."
                    else:
                        preview = "[]"
                    preview += size_info
                value_str = preview
            elif isinstance(value, bool):
                value_str = "[green]✓[/green]" if value else "[red]✗[/red]"
            elif isinstance(value, str):
                if len(value) > 50:
                    value_str = value[:47] + "..."
                elif value.startswith(("http://", "https://")):
                    value_str = f"[link]{value}[/link]"
                elif value.lower() in ["true", "false"]:
                    value_str = f"[cyan]{value}[/cyan]"
                else:
                    value_str = value
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    value_str = f"{value:.3f}" if abs(value) < 1000 else f"{value:.2e}"
                else:
                    value_str = f"{value:,}" if abs(value) > 1000 else str(value)
            elif value is None:
                value_str = "[dim]null[/dim]"
            else:
                value_str = str(value)

            table.add_row(str(key), value_str, value_type)

        return table

    def _create_data_table(
        self, data: Union[List[dict], dict], title: str = "Data"
    ) -> Table:
        """Create a dynamic table from list of dictionaries or tabular dict with intelligent column formatting."""
        if isinstance(data, dict) and self._is_tabular_dict(data):
            # Convert tabular dict to list of dicts
            keys = list(data.keys())
            values = list(data.values())
            rows = []
            for i in range(len(values[0])):
                row = {key: values[j][i] for j, key in enumerate(keys)}
                rows.append(row)
            data = rows

        if not isinstance(data, list) or not data:
            return None

        # Get column headers from first item
        first_item = data[0]
        if not isinstance(first_item, dict):
            return None

        headers = list(first_item.keys())

        # Analyze column types and content for intelligent formatting
        column_analysis = {}
        for header in headers:
            values = [item.get(header) for item in data[:10]]  # Sample first 10 rows
            non_null_values = [v for v in values if v is not None]

            if not non_null_values:
                column_analysis[header] = {"type": "null", "width": 10, "style": "dim"}
                continue

            # Determine predominant type
            types = [type(v).__name__ for v in non_null_values]
            most_common_type = max(set(types), key=types.count)

            # Analyze content for formatting hints
            analysis = {
                "type": most_common_type,
                "max_length": max(len(str(v)) for v in non_null_values),
                "has_urls": any(
                    isinstance(v, str) and v.startswith(("http://", "https://"))
                    for v in non_null_values
                ),
                "is_boolean_like": all(
                    isinstance(v, bool)
                    or (
                        isinstance(v, str)
                        and v.lower() in ["true", "false", "yes", "no"]
                    )
                    for v in non_null_values
                ),
                "is_numeric": most_common_type in ["int", "float"],
                "is_id_like": header.lower() in ["id", "name", "title", "key"]
                or header.lower().endswith("_id"),
            }

            # Determine display properties with better width handling for common data patterns
            if analysis["is_id_like"]:
                analysis["style"] = "cyan"
                # Give more space for dataset IDs and similar identifiers
                analysis["width"] = min(25, max(15, analysis["max_length"] + 2))
            elif analysis["is_boolean_like"]:
                analysis["style"] = "green"
                analysis["width"] = 8
            elif analysis["is_numeric"]:
                analysis["style"] = "yellow"
                analysis["width"] = min(15, max(8, analysis["max_length"] + 2))
            elif analysis["has_urls"]:
                analysis["style"] = "blue"
                analysis["width"] = 30
            elif header.lower() in ["description", "content", "message", "text"]:
                analysis["style"] = "white"
                analysis["width"] = 40
            elif "time" in header.lower() or "date" in header.lower():
                # Special handling for timestamps and dates
                analysis["style"] = "blue"
                analysis["width"] = min(22, max(15, analysis["max_length"] + 2))
            elif (
                header.lower().endswith(("_id", "_name")) or "dataset" in header.lower()
            ):
                # Special handling for BigQuery-style fields
                analysis["style"] = "cyan"
                analysis["width"] = min(30, max(18, analysis["max_length"] + 2))
            else:
                analysis["style"] = "white"
                analysis["width"] = min(25, max(12, analysis["max_length"] + 2))

            column_analysis[header] = analysis

        # Create table with intelligent column formatting
        table = Table(
            title=f"{title} ({len(data)} rows)", show_header=True, header_style="cyan"
        )

        for header in headers:
            col_info = column_analysis[header]

            # Smart header formatting for common BigQuery/database fields
            if "_" in header:
                # Convert snake_case to Title Case
                display_header = " ".join(
                    word.capitalize() for word in header.split("_")
                )
            else:
                display_header = str(header).title()

            table.add_column(
                display_header,
                style=col_info["style"],
                width=col_info["width"],
                overflow="ellipsis",
            )

        # Add rows with intelligent value formatting
        max_rows = getattr(self, "max_display_rows", 25)
        for i, item in enumerate(data[:max_rows]):
            if not isinstance(item, dict):
                continue

            row = []
            for header in headers:
                value = item.get(header, "")
                col_info = column_analysis[header]

                # Format different data types intelligently
                if value is None:
                    formatted = "[dim]—[/dim]"  # Use em dash for null values
                elif isinstance(value, bool):
                    formatted = "[green]✓[/green]" if value else "[red]✗[/red]"
                elif col_info["is_boolean_like"] and isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        formatted = "[green]✓[/green]"
                    elif value.lower() in ["false", "no", "0"]:
                        formatted = "[red]✗[/red]"
                    else:
                        formatted = value
                elif isinstance(value, (int, float)):
                    if isinstance(value, float):
                        formatted = (
                            f"{value:.3f}" if abs(value) < 1000 else f"{value:.2e}"
                        )
                    else:
                        formatted = f"{value:,}" if abs(value) > 1000 else str(value)
                elif isinstance(value, str):
                    if col_info["has_urls"]:
                        formatted = (
                            f"[link]{value}[/link]"
                            if len(value) < 35
                            else f"[link]{value[:32]}...[/link]"
                        )
                    elif len(value) > col_info["width"] - 3:
                        # Smart truncation - try to keep meaningful parts
                        if ":" in value and len(value) > 20:  # For full dataset IDs
                            parts = value.split(":")
                            if len(parts) == 2:
                                # Show project:dataset format smartly
                                available_space = (
                                    col_info["width"] - 6
                                )  # Account for "..." and ":"
                                project_space = available_space // 2
                                dataset_space = available_space - project_space
                                formatted = f"{parts[0][:project_space]}...:{parts[1][:dataset_space]}..."
                            else:
                                formatted = value[: col_info["width"] - 3] + "..."
                        else:
                            formatted = value[: col_info["width"] - 3] + "..."
                    else:
                        formatted = value
                elif isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        formatted = f"[{len(value)} items]"
                    else:
                        formatted = f"{{{len(value)} keys}}"
                else:
                    formatted = (
                        str(value)
                        if len(str(value)) < col_info["width"]
                        else str(value)[: col_info["width"] - 3] + "..."
                    )

                row.append(formatted)

            table.add_row(*row)

        # Add info if truncated
        if len(data) > max_rows:
            table.caption = f"Showing {max_rows} of {len(data)} rows"

        return table

    def _create_list_display(
        self, data: list, title: str = "Items"
    ) -> Union[Table, Panel]:
        """Create display for simple lists."""
        max_items = getattr(self, "max_display_rows", 20)
        if len(data) <= 10 and all(
            isinstance(item, (str, int, float)) for item in data
        ):
            # Small list of simple values - use columns
            items = [str(item) for item in data]
            return Columns(items, equal=True, expand=True, title=title)
        else:
            # Larger or complex list - use panel
            content = "\n".join(f"• {item}" for item in data[:max_items])
            if len(data) > max_items:
                content += f"\n... and {len(data) - max_items} more items"
            return Panel(
                content, title=f"{title} ({len(data)} items)", border_style="blue"
            )

    def beautify_json(self, data: Any, title: str = "Response") -> None:
        """Display JSON data in a beautified format with intelligent formatting."""
        # Analyze data structure for intelligent display
        analysis = self._analyze_data_types(data)
        structure_type = analysis["best_display"]

        # Check for special cases first (before generic structure-based routing)
        if (
            isinstance(data, dict)
            and "tools" in data
            and isinstance(data["tools"], list)
        ):
            # Special case: handle tools lists (MCP-specific but common pattern)
            tools = data["tools"]
            if tools and isinstance(tools[0], dict) and "name" in tools[0]:
                self.beautify_tools_list(tools, "MCP Server Tools")
                return
            # Tools is just names or other simple data - fall through to generic display

        # Route to appropriate display method based on analysis
        if structure_type == "data_service" and isinstance(data, dict):
            # Handle data service responses (BigQuery, databases, etc.)
            self._display_data_service_response(data, title)

        elif structure_type == "key_value" and isinstance(data, dict):
            table = self._create_key_value_table(data, title)
            self.console.print(table)

        elif structure_type == "table":
            table = self._create_data_table(data, title)
            if table:
                self.console.print(table)
            else:
                # Fallback to JSON
                self._display_json_syntax(data, title)

        elif structure_type == "list" and isinstance(data, list):
            display = self._create_list_display(data, title)
            self.console.print(display)

        elif structure_type == "tree" and isinstance(data, dict):
            # Use tree display for hierarchical data
            self._display_tree_structure(data, title)

        elif structure_type == "empty":
            self.console.print(f"[dim]{title}: Empty collection[/dim]")

        elif structure_type == "text":
            self.console.print(Panel(str(data), title=title, border_style="blue"))

        else:
            # Default to syntax-highlighted JSON with analysis hints
            self._display_json_syntax(data, title, analysis)

    def _display_data_service_response(
        self, data: dict, title: str = "Data Service Response"
    ) -> None:
        """
        Display data service responses with tabular data and metadata.

        Common patterns:
        - BigQuery: {datasets: [...], total_count: n, message: "..."}
        - Database queries: {rows: [...], count: n, execution_time: "..."}
        """
        # Find the main data list
        list_keys = [
            "datasets",
            "rows",
            "records",
            "results",
            "data",
            "items",
            "entries",
        ]
        main_data_key = None
        main_data = None

        for key in list_keys:
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                main_data_key = key
                main_data = data[key]
                break

        if not main_data_key or not main_data:
            # Fallback to tree display if we can't find the expected structure
            self._display_tree_structure(data, title)
            return

        # Create a table for the main data
        table = self._create_data_table(main_data, f"{title} - {main_data_key.title()}")
        if table:
            self.console.print(table)
        else:
            # Fallback if table creation fails
            self._display_json_syntax(main_data, f"{title} - {main_data_key.title()}")

        # Display metadata in a compact format
        metadata = {k: v for k, v in data.items() if k != main_data_key}
        if metadata:
            # Create a compact metadata display
            metadata_items = []
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    if isinstance(value, bool):
                        display_value = "✓" if value else "✗"
                    elif isinstance(value, str) and len(value) > 50:
                        display_value = f"{value[:47]}..."
                    else:
                        display_value = str(value)

                    metadata_items.append(f"[cyan]{key}[/]: {display_value}")
                elif value is None:
                    metadata_items.append(f"[cyan]{key}[/]: [dim]null[/dim]")
                else:
                    metadata_items.append(
                        f"[cyan]{key}[/]: [yellow]{type(value).__name__}[/yellow]"
                    )

            if metadata_items:
                metadata_text = " | ".join(metadata_items)
                self.console.print(f"\n[dim]ℹ️  {metadata_text}[/dim]")

    def _display_tree_structure(self, data: dict, title: str = "Data") -> None:
        """Display hierarchical data as a tree structure."""
        tree = Tree(f"[bold cyan]{title}[/bold cyan]")

        def add_to_tree(node, key, value, max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                node.add(f"[dim]{key}: ... (truncated)[/dim]")
                return

            if isinstance(value, dict):
                if len(value) > 10:  # Large dicts get summary
                    branch = node.add(f"[yellow]{key}[/yellow] ({len(value)} items)")
                    # Show first few items
                    for i, (k, v) in enumerate(list(value.items())[:3]):
                        add_to_tree(branch, k, v, max_depth, current_depth + 1)
                    if len(value) > 3:
                        branch.add("[dim]... more items[/dim]")
                else:
                    branch = node.add(f"[yellow]{key}[/yellow]")
                    for k, v in value.items():
                        add_to_tree(branch, k, v, max_depth, current_depth + 1)
            elif isinstance(value, list):
                if len(value) > 5:  # Large lists get summary
                    branch = node.add(f"[magenta]{key}[/magenta] [{len(value)} items]")
                    for i, item in enumerate(value[:3]):
                        add_to_tree(
                            branch, f"[{i}]", item, max_depth, current_depth + 1
                        )
                    if len(value) > 3:
                        branch.add("[dim]... more items[/dim]")
                else:
                    branch = node.add(f"[magenta]{key}[/magenta]")
                    for i, item in enumerate(value):
                        add_to_tree(
                            branch, f"[{i}]", item, max_depth, current_depth + 1
                        )
            else:
                # Format leaf values
                if isinstance(value, bool):
                    display_value = "✓" if value else "✗"
                elif isinstance(value, str) and len(value) > 50:
                    display_value = f"{value[:47]}..."
                else:
                    display_value = str(value)

                node.add(f"[white]{key}[/white]: [green]{display_value}[/green]")

        for key, value in data.items():
            add_to_tree(tree, key, value)

        self.console.print(tree)

    def _display_json_syntax(
        self, data: Any, title: str, analysis: Dict[str, Any] = None
    ) -> None:
        """Display data as syntax-highlighted JSON with optional analysis hints."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If it's not valid JSON, display as text
                self.console.print(Panel(data, title=title, border_style="blue"))
                return

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)

        # Add analysis hints as caption if provided
        caption = None
        if analysis:
            hints = []
            if analysis.get("complexity"):
                hints.append(f"Complexity: {analysis['complexity']}")
            if analysis.get("size"):
                hints.append(f"Size: {analysis['size']} items")
            if analysis.get("structure_hints"):
                hints.append(f"Structure: {', '.join(analysis['structure_hints'])}")
            if hints:
                caption = " | ".join(hints)

        panel = Panel(syntax, title=title, border_style="green")
        if caption:
            panel.subtitle = f"[dim]{caption}[/dim]"

        self.console.print(panel)

    def _get_template_formatter(self, template_name: str):
        """Get template-specific formatter if available."""
        try:
            import importlib.util
            from pathlib import Path

            # Look for response_formatter.py in the template directory
            template_dir = (
                Path(__file__).parent.parent / "template" / "templates" / template_name
            )
            formatter_path = template_dir / "response_formatter.py"

            if formatter_path.exists():
                spec = importlib.util.spec_from_file_location(
                    f"{template_name}_formatter", formatter_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for the formatter class (convention: <Template>ResponseFormatter)
                formatter_class_name = f"{template_name.replace('-', '').replace('_', '').title()}ResponseFormatter"

                # Fallback to common names
                possible_names = [
                    formatter_class_name,
                    "ElasticsearchResponseFormatter",
                    "ResponseFormatter",
                    "Formatter",
                ]

                for class_name in possible_names:
                    if hasattr(module, class_name):
                        formatter_class = getattr(module, class_name)
                        return formatter_class(console=self.console)

        except Exception as e:
            if self.verbose:
                self.console.print(f"[dim]Could not load template formatter: {e}[/dim]")

        return None

    def _get_template_formatter(self, template_name: str):
        """Get template-specific formatter if available."""
        try:
            import importlib
            import sys

            template_path = TEMPLATES_DIR / template_name

            if not template_path.exists():
                return None

            # Check for template.json configuration first
            template_json_path = template_path / "template.json"
            formatter_config = None

            if template_json_path.exists():
                try:
                    with open(template_json_path, "r") as f:
                        template_data = json.load(f)
                        formatter_config = template_data.get("response_formatter", {})

                        # Skip if explicitly disabled
                        if formatter_config.get("enabled", True) is False:
                            return None
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

            # Determine module and class names
            if formatter_config:
                module_name = formatter_config.get("module", "response_formatter")
                class_name = formatter_config.get("class")
            else:
                module_name = "response_formatter"
                class_name = None

            # Check if formatter module exists
            formatter_file = template_path / f"{module_name}.py"
            if not formatter_file.exists():
                return None

            # Import the formatter module
            sys.path.insert(0, str(template_path))
            try:
                formatter_module = importlib.import_module(module_name)

                # Find the formatter class
                if class_name:
                    # Use explicitly configured class name
                    if hasattr(formatter_module, class_name):
                        formatter_class = getattr(formatter_module, class_name)
                    else:
                        if self.verbose:
                            self.console.print(
                                f"[yellow]Configured formatter class '{class_name}' not found[/yellow]"
                            )
                        return None
                else:
                    # Auto-detect formatter class
                    formatter_class = self._find_formatter_class(
                        formatter_module, template_name
                    )

                if formatter_class:
                    return formatter_class(console=self.console)

            finally:
                if str(template_path) in sys.path:
                    sys.path.remove(str(template_path))

            return None

        except Exception as e:
            if self.verbose:
                self.console.print(
                    f"[yellow]Failed to load template formatter: {e}[/yellow]"
                )
            return None

    def _find_formatter_class(self, module, template_name: str):
        """Find formatter class in module using naming conventions."""
        # Try multiple naming conventions
        possible_names = [
            "ElasticsearchResponseFormatter",  # Special case for elasticsearch
            f"{template_name.replace('-', '_').title().replace('_', '')}ResponseFormatter",
            f"{''.join(word.title() for word in template_name.replace('-', '_').split('_'))}ResponseFormatter",
        ]

        for class_name in possible_names:
            if hasattr(module, class_name):
                return getattr(module, class_name)

        # Look for any class ending with ResponseFormatter
        for attr_name in dir(module):
            if attr_name.endswith("ResponseFormatter") and not attr_name.startswith(
                "_"
            ):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):  # Check if it's a class
                    return attr

        return None

    def _extract_response_text(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract the actual response text from MCP response structure."""
        try:
            if "result" in response and response["result"]:
                result_data = response["result"]

                # Handle MCP content format
                if isinstance(result_data, dict) and "content" in result_data:
                    content_items = result_data["content"]
                    if isinstance(content_items, list) and content_items:
                        for content in content_items:
                            if isinstance(content, dict) and "text" in content:
                                return content["text"]

                # Handle direct string result
                elif isinstance(result_data, str):
                    return result_data

        except Exception:
            pass

        return None

    def _print_truncation_hint(self, data: Any) -> None:
        """Print a small hint if a dataset/list was truncated by the display limit."""
        try:
            max_rows = getattr(self, "max_display_rows", 100)
            # For dicts with lists under common keys
            if isinstance(data, dict):
                # Check common tabular keys
                for key in ("rows", "results", "data", "items", "records", "datasets"):
                    if key in data and isinstance(data[key], list):
                        total = len(data[key])
                        if total > max_rows:
                            more = total - max_rows
                            self.console.print(
                                f"[dim]... and {more} more {key} (showing {max_rows})[/dim]"
                            )
                            return
            # For top-level lists
            if isinstance(data, list):
                total = len(data)
                if total > max_rows:
                    more = total - max_rows
                    self.console.print(
                        f"[dim]... and {more} more items (showing {max_rows})[/dim]"
                    )
        except Exception:
            return

    def beautify_tool_response(
        self, response: Dict[str, Any], template_name: str = None, tool_name: str = None
    ) -> None:
        """Beautify tool execution response with enhanced formatting."""
        # First try template-specific formatter if available
        if template_name and tool_name:
            try:
                template_formatter = self._get_template_formatter(template_name)
                if template_formatter:
                    # Extract the actual response text
                    response_text = self._extract_response_text(response)
                    if response_text:
                        template_formatter.format_tool_response(
                            tool_name, response_text
                        )
                        return
            except Exception as e:
                if self.verbose:
                    self.console.print(
                        f"[yellow]⚠️  Template formatter failed: {e}[/yellow]"
                    )
                # Continue with default formatting

        # Fallback to default formatting
        if response.get("used_stdio"):
            self.console.print(
                Panel(
                    f"[dim]⚠️  Note: Tool executed via stdio interface on {response.get('backend_type', 'unknown')} backend.[/dim]",
                    border_style="yellow",
                )
            )

        if response.get("success"):
            try:
                if "result" in response and response["result"]:
                    result_data = response["result"]

                    # Handle MCP content format - prioritize structuredContent
                    if (
                        isinstance(result_data, dict)
                        and "structuredContent" in result_data
                    ):
                        # Use structuredContent when available (already parsed JSON)
                        structured_data = result_data["structuredContent"]

                        # Check if this looks like a BigQuery or database response
                        if self._is_data_service_response(structured_data):
                            self._display_data_service_response(
                                structured_data, TOOL_RESULT_TITLE
                            )
                        else:
                            self.beautify_json(structured_data, TOOL_RESULT_TITLE)
                        # After display, show truncation hint if applicable
                        try:
                            self._print_truncation_hint(structured_data)
                        except Exception:
                            pass

                    elif isinstance(result_data, dict) and "content" in result_data:
                        content_items = result_data["content"]
                        if isinstance(content_items, list) and content_items:
                            for i, content in enumerate(content_items):
                                if isinstance(content, dict) and "text" in content:
                                    # Display text content as-is
                                    text_content = content["text"]

                                    # Try to parse as JSON for better formatting
                                    try:
                                        parsed_content = json.loads(text_content)

                                        # Check if parsed content is a data service response
                                        if self._is_data_service_response(
                                            parsed_content
                                        ):
                                            self._display_data_service_response(
                                                parsed_content,
                                                f"{TOOL_RESULT_TITLE} {i + 1}",
                                            )
                                        else:
                                            self.beautify_json(
                                                parsed_content,
                                                f"{TOOL_RESULT_TITLE} {i + 1}",
                                            )
                                        try:
                                            self._print_truncation_hint(parsed_content)
                                        except Exception:
                                            pass
                                    except json.JSONDecodeError:
                                        # Display as text if not JSON
                                        self.console.print(
                                            Panel(
                                                text_content,
                                                title=f"{TOOL_RESULT_TITLE} {i + 1}",
                                                border_style="green",
                                            )
                                        )
                                else:
                                    self.beautify_json(content, f"Content {i + 1}")
                        else:
                            self.beautify_json(result_data, TOOL_RESULT_TITLE)
                            try:
                                self._print_truncation_hint(result_data)
                            except Exception:
                                pass
                    else:
                        self.beautify_json(result_data, TOOL_RESULT_TITLE)
                        try:
                            self._print_truncation_hint(result_data)
                        except Exception:
                            pass

                elif "error" in response and response.get("error"):
                    error_info = response["error"]
                    self.console.print(
                        Panel(
                            f"Error {error_info.get('code', 'unknown')}: {error_info.get('message', 'Unknown error')}",
                            title="Tool Error",
                            border_style="red",
                        )
                    )
                else:
                    self.beautify_json(response, "MCP Response")

            except Exception as e:
                # Debug the exception and fallback to raw output
                if self.verbose:
                    self.console.print(
                        f"[yellow]⚠️  Beautifier parsing error: {e}[/yellow]"
                    )
                    self.console.print(
                        f"[dim]Traceback: {traceback.format_exc()}[/dim]"
                    )
                # Fallback to raw output
                self.console.print(
                    Panel(
                        response.get("result"), title="Tool Output", border_style="blue"
                    )
                )
        else:
            # Failed execution
            error_msg = response.get("error", "Unknown error")

            self.console.print(
                Panel(
                    f"Execution failed: {error_msg}",
                    title="Execution Error",
                    border_style="red",
                )
            )

    def beautify_tools_list(
        self,
        tools: List[Dict[str, Any]],
        source: str = "Template",
        discovery_method: str = "unknown",
        backend: str = "unknown",
        template_name: str = "unknown",
    ) -> None:
        """Beautify tools list display with discovery metadata."""
        if not tools:
            self.console.print("[yellow]⚠️  No tools found[/yellow]")
            return

        # Create discovery metadata display
        discovery_info = (
            f"Backend: {backend} | Method: {discovery_method} | Source: {source}"
        )

        # Create tools table with enhanced title
        table = Table(
            title=f"Tools from '{template_name}' ({len(tools)} found) - {discovery_info}",
            header_style="bold cyan",
            show_lines=True,  # Add lines between rows for spacing
        )
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Parameters", style="yellow", width=50)
        table.add_column("Category", style="green", width=15)

        for tool in tools:
            name = tool.get("name", "Unknown")
            description = tool.get("description", "No description")

            # Handle parameters
            parameters = tool.get("parameters", {})
            input_schema = tool.get("inputSchema", {})

            # Check both formats - MCP tools/call format and discovery format
            if isinstance(parameters, dict) and "properties" in parameters:
                properties = parameters.get("properties", {})
                param_count = len(properties)
                param_text = f"{param_count} params"
                param_names = ", ".join(properties.keys())
            elif isinstance(input_schema, dict) and "properties" in input_schema:
                properties = input_schema.get("properties", {})
                param_count = len(properties)
                param_text = f"{param_count} params"
                param_names = ", ".join(properties.keys())
            elif isinstance(parameters, list):
                param_count = len(parameters)
                param_text = f"{param_count} params"
                param_names = ", ".join([p.get("name", "Unknown") for p in parameters])
            elif parameters or input_schema:
                param_text = "Schema defined"
                param_names = ""
            else:
                param_text = "0 params"
                param_names = ""

            category = tool.get("category", "general")

            table.add_row(
                name,
                description,
                param_text + " (" + param_names + ")" if param_names else "",
                category,
            )

        self.console.print(table)

        # Show detailed discovery information
        discovery_hints = {
            "stdio": "🔗 Tools discovered via stdio interface (direct container communication)",
            "http": "🌐 Tools discovered via HTTP API (from running server)",
            "static": "📄 Tools discovered from template definition files",
            "cache": "💾 Tools loaded from cache (use --force-refresh for latest)",
            "error": "❌ Error occurred during discovery",
        }

        hint = discovery_hints.get(
            discovery_method, f"ℹ️  Discovery method: {discovery_method}"
        )
        self.console.print(f"[dim]{hint}[/dim]")

        # Show additional metadata
        if backend != "unknown":
            self.console.print(
                f"[dim]💡 Using {backend} backend for container operations[/dim]"
            )

    def beautify_deployed_servers(self, servers: List[Dict[str, Any]]) -> None:
        """Beautify deployed servers list."""
        if not servers:
            self.console.print("[yellow]⚠️  No deployed servers found[/yellow]")
            return

        table = Table(title=f"Deployed MCP Servers ({len(servers)} active)")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Transport", style="yellow", width=12)
        table.add_column("Status", style="green", width=10)
        table.add_column("Endpoint", style="blue", width=30)
        table.add_column("Ports", style="blue", width=20)
        table.add_column("Since", style="blue", width=25)
        table.add_column("Tools", style="magenta", width=10)

        for server in servers:
            id = server.get("id", "N/A")
            template_name = server.get("name", "Unknown")
            transport = server.get("transport", "unknown")
            status = server.get("status", "unknown")
            endpoint = server.get("endpoint", "N/A")
            ports = server.get("ports", "N/A")
            since = server.get("since", "N/A")
            tool_count = len(server.get("tools", []))

            # Color status
            if status == "running":
                status_text = f"[green]{status}[/green]"
            elif status == "failed":
                status_text = f"[red]{status}[/red]"
            else:
                status_text = f"[yellow]{status}[/yellow]"

            table.add_row(
                id,
                template_name,
                transport,
                status_text,
                endpoint,
                ports,
                since,
                str(tool_count),
            )

        self.console.print(table)

    def beautify_deployed_servers_grouped(
        self, grouped_deployments: Dict[str, List[Dict]], show_empty: bool = False
    ) -> None:
        """
        Render deployments grouped by backend with visual separation.

        Args:
            grouped_deployments: Dictionary mapping backend_type to deployment list
            show_empty: Whether to show backends with no deployments
        """
        if not grouped_deployments and not show_empty:
            self.console.print("[dim]No deployments found.[/]")
            return

        for backend_type in VALID_BACKENDS:  # Production backends only
            deployments = grouped_deployments.get(backend_type, [])

            if not deployments and not show_empty:
                continue

            # Backend header
            backend_indicator = get_backend_indicator(backend_type)
            count_text = (
                f"({len(deployments)} deployment{'s' if len(deployments) != 1 else ''})"
            )
            header = f"{backend_indicator} {count_text}"

            self.console.print(f"\n{header}")

            if not deployments:
                self.console.print("  No deployments")
                continue

            # Create table for this backend's deployments
            table = Table(show_header=True, header_style="cyan", padding=(0, 1))
            table.add_column("ID", style="cyan", width=15)
            table.add_column("Template", style="white", width=15)
            table.add_column("Status", style="white", width=10)
            table.add_column("Endpoint", style="blue", width=30)
            table.add_column("Ports", style="blue", width=20)
            table.add_column("Transport", style="yellow", width=10)
            table.add_column("Since", style="blue", width=10)

            for deployment in deployments:
                deployment_id = deployment.get(
                    "id", deployment.get("name", deployment.get("deployment_id", "N/A"))
                )[:14]
                template = deployment.get("template", "unknown")
                status = deployment.get("status", "unknown")
                endpoint = deployment.get("endpoint", "unknown")
                ports = deployment.get("ports", deployment.get("port", "unknown"))
                transport = deployment.get("transport", "unknown")
                created = format_timestamp(
                    deployment.get("created", deployment.get("since"))
                )

                # Colorize status
                status_color = get_status_color(status)
                status_text = f"[{status_color}]● {status}[/]"

                table.add_row(
                    deployment_id,
                    template,
                    status_text,
                    endpoint,
                    ports,
                    transport,
                    created,
                )

            self.console.print(table)

    def beautify_logs(
        self,
        logs: Union[str, Dict[str, List[Dict[str, str]]]],
        deployment_id: str = None,
        title: str = "Deployment Logs",
    ) -> None:
        """
        Beautify logs output for single or multiple deployments/backends.

        Args:
            logs: str for single deployment, or dict of backend -> list of {deployment_id: logs}
            deployment_id: Optional deployment id for single log
            title: Title for display
        """
        if isinstance(logs, str):
            panel_title = (
                f"Logs for Deployment {deployment_id}" if deployment_id else title
            )
            self.console.print(Panel(logs, title=panel_title, border_style="blue"))
            # Show follow hint
            if deployment_id:
                self.console.print("[dim]To stream logs, run:[/dim]")
                self.console.print(f"[blue]docker logs -f {deployment_id}[/blue]")
            return

        if isinstance(logs, dict):
            for backend_type, deployments in logs.items():
                backend_indicator = get_backend_indicator(backend_type)
                self.console.print(f"\n{backend_indicator} Logs")
                if not deployments:
                    self.console.print("  No logs found.")
                    continue
                for i, dep in enumerate(deployments):
                    for dep_id, dep_logs in dep.items():
                        panel_title = f"Deployment {dep_id}"
                        self.console.print(
                            Panel(
                                dep_logs or "[dim]No logs available[/dim]",
                                title=panel_title,
                                border_style=get_backend_color(backend_type),
                            )
                        )
                        self.console.print("[dim]To stream logs, run:[/dim]")
                        if backend_type == "docker":
                            self.console.print(f"[blue]docker logs -f {dep_id}[/blue]")
                        elif backend_type == "kubernetes":
                            self.console.print(
                                f"[green]kubectl logs -f {dep_id}[/green]"
                            )
                        else:
                            self.console.print(
                                f"[yellow]No follow command available for backend '{backend_type}'[/yellow]"
                            )
                    # Add a separator between deployments for readability
                    if i < len(deployments) - 1:
                        self.console.rule(
                            "[dim]--- Next Deployment ---[/dim]",
                            style=get_backend_color(backend_type),
                        )
            return
        self.console.print(Panel(str(logs), title=title, border_style="blue"))

    def render_backend_health_status(self, health_data: Dict[str, Any]) -> None:
        """
        Render health status for all backends.

        Args:
            health_data: Health status data by backend
        """
        self.console.print("\n[bold]Backend Health Status[/]")

        panels = []
        for backend_type in VALID_BACKENDS:
            if backend_type not in health_data:
                continue

            health = health_data[backend_type]
            status = health.get("status", "unknown")
            deployment_count = health.get("deployment_count", 0)
            error = health.get("error")

            # Choose colors and icons based on status
            if status == "healthy":
                status_color = "green"
                status_icon = "✅"
            else:
                status_color = "red"
                status_icon = "❌"

            backend_icon = get_backend_icon(backend_type)
            backend_color = get_backend_color(backend_type)

            # Panel content
            content = f"[{status_color}]{status_icon} {status.upper()}[/]\n"
            content += f"Deployments: {deployment_count}"

            if error:
                content += f"\n[red]Error: {error[:40]}[/]"

            panel = Panel(
                content,
                title=f"[{backend_color}]{backend_icon} {backend_type.upper()}[/]",
                border_style=backend_color,
                width=20,
            )
            panels.append(panel)

        if panels:
            self.console.print(Columns(panels, equal=True))
        else:
            self.console.print("[dim]No backend health data available.[/]")
