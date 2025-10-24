"""
Bulk Registration Utilities for MCP Servers

Convenience wrappers over FastMCP's add_tool() and remove_tool() methods for
config-driven tool management with batch error handling.

What this module provides:
- Config-driven registration as alternative to manual loops of add_tool() calls
- Batch error handling with success/failure reporting
- Convenient lifecycle operations (bulk remove, replace, conditional removal)

What it doesn't provide:
- This is not a replacement for FastMCP - it uses FastMCP's methods internally
- This is not a different tool registry - it calls FastMCP's existing registry
- This is not eliminating decorators - it provides an alternative pattern

Core implementation:
    bulk_register_tools() essentially does:
    for tool_name, config in tools_config.items():
        server.add_tool(config["function"], name=tool_name, description=...)
    Plus error handling, logging, and reporting.
"""

import logging
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class BulkRegistrationError(Exception):
    """Exception raised during bulk tool registration."""

    pass


def bulk_register_tools(
    srv: FastMCP, tools_config: dict[str, dict[str, Any]]
) -> list[tuple[str, str]]:
    """
    Bulk register MCP tools from configuration.

    This function replaces manual @srv.tool() decorations by automatically
    registering the business logic functions directly.

    Args:
        srv: FastMCP server instance to register tools with
        tools_config: Dictionary mapping tool names to their configuration.
                     Each config should have:
                     - 'function': The callable function to register
                     - 'description': Description of the tool

    Returns:
        List of tuples (tool_name, description) for registered tools

    Raises:
        BulkRegistrationError: If registration fails for any tool

    Example:
        tools_config = {
            "get_weather": {
                "function": weather_service.get_current_weather,
                "description": "Get current weather information"
            }
        }
        registered = bulk_register_tools(srv, tools_config)
    """
    logger.info(f"Starting bulk registration of {len(tools_config)} MCP tools...")

    registered_tools = []
    registration_errors = []

    for tool_name, config in tools_config.items():
        try:
            # Get function and metadata
            tool_function = config["function"]
            description = config.get("description", f"Tool: {tool_name}")

            # Validate function is callable
            if not callable(tool_function):
                raise BulkRegistrationError(
                    f"Tool '{tool_name}' function is not callable"
                )

            # Register the tool directly with FastMCP using add_tool
            srv.add_tool(tool_function, name=tool_name, description=description)

            registered_tools.append((tool_name, description))
            logger.debug(f"Successfully registered tool: {tool_name}")

        except Exception as e:
            error_msg = f"Failed to register tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            registration_errors.append(error_msg)

    # Report results
    if registration_errors:
        error_summary = f"Registration failed for {len(registration_errors)} tools: {registration_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)

    logger.info(f"Successfully registered {len(registered_tools)} MCP tools")
    return registered_tools


def bulk_register_with_adapter_pattern(
    srv: FastMCP, tools_config: dict[str, dict[str, Any]], adapter_function: Callable
) -> list[tuple[str, str]]:
    """
    Bulk register MCP tools using an adapter pattern for use cases.

    This variant is useful when you have use case classes that need to be adapted
    to MCP format using an adapter function (like create_mcp_adapter).

    Args:
        srv: FastMCP server instance to register tools with
        tools_config: Dictionary mapping tool names to their configuration.
                     Each config should have:
                     - 'use_case': The use case instance or callable
                     - 'description': Description of the tool
        adapter_function: Function to adapt use cases to MCP format

    Returns:
        List of tuples (tool_name, description) for registered tools

    Raises:
        BulkRegistrationError: If registration fails for any tool

    Example:
        from mcp_commons import create_mcp_adapter

        tools_config = {
            "list_projects": {
                "use_case": ListProjectsUseCase(project_service).execute,
                "description": "List all available projects"
            }
        }
        registered = bulk_register_with_adapter_pattern(srv, tools_config, create_mcp_adapter)
    """
    logger.info(
        f"Starting bulk registration with adapter pattern of {len(tools_config)} MCP tools..."
    )

    registered_tools = []
    registration_errors = []

    for tool_name, config in tools_config.items():
        try:
            # Get use case and metadata
            use_case = config["use_case"]
            description = config.get("description", f"Tool: {tool_name}")

            # Validate use case is callable
            if not callable(use_case):
                raise BulkRegistrationError(
                    f"Tool '{tool_name}' use case is not callable"
                )

            # Create adapted function using provided adapter
            adapted_function = adapter_function(use_case)

            # Register the adapted tool with FastMCP
            srv.add_tool(adapted_function, name=tool_name, description=description)

            registered_tools.append((tool_name, description))
            logger.debug(f"Successfully registered adapted tool: {tool_name}")

        except Exception as e:
            error_msg = f"Failed to register adapted tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            registration_errors.append(error_msg)

    # Report results
    if registration_errors:
        error_summary = f"Registration failed for {len(registration_errors)} tools: {registration_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)

    logger.info(f"Successfully registered {len(registered_tools)} adapted MCP tools")
    return registered_tools


def bulk_register_tuple_format(
    srv: FastMCP, tool_tuples: list[tuple[Callable, str, str]]
) -> list[tuple[str, str]]:
    """
    Bulk register MCP tools from a list of (function, name, description) tuples.

    This format is compatible with existing bulk registration systems that
    return tuples from their configuration processing.

    Args:
        srv: FastMCP server instance to register tools with
        tool_tuples: List of (function, name, description) tuples

    Returns:
        List of tuples (tool_name, description) for registered tools

    Raises:
        BulkRegistrationError: If registration fails for any tool

    Example:
        tool_tuples = [
            (weather_function, "get_weather", "Get current weather"),
            (time_function, "get_time", "Get current time")
        ]
        registered = bulk_register_tuple_format(srv, tool_tuples)
    """
    logger.info(
        f"Starting bulk registration of {len(tool_tuples)} MCP tools from tuple format..."
    )

    registered_tools = []
    registration_errors = []

    for function, tool_name, description in tool_tuples:
        try:
            # Validate function is callable
            if not callable(function):
                raise BulkRegistrationError(
                    f"Tool '{tool_name}' function is not callable"
                )

            # Register the tool with FastMCP
            srv.add_tool(function, name=tool_name, description=description)

            registered_tools.append((tool_name, description))
            logger.debug(f"Successfully registered tuple tool: {tool_name}")

        except Exception as e:
            error_msg = f"Failed to register tuple tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            registration_errors.append(error_msg)

    # Report results
    if registration_errors:
        error_summary = f"Registration failed for {len(registration_errors)} tools: {registration_errors}"
        logger.error(error_summary)
        raise BulkRegistrationError(error_summary)

    logger.info(
        f"Successfully registered {len(registered_tools)} tuple format MCP tools"
    )
    return registered_tools


def log_registration_summary(
    registered_tools: list[tuple[str, str]],
    total_configured: int,
    server_name: str = "MCP Server",
) -> None:
    """
    Log a summary of the registration process.

    Args:
        registered_tools: List of successfully registered tool tuples (name, description)
        total_configured: Total number of tools that were configured
        server_name: Name of the server for logging
    """
    logger.info(f"=== {server_name} Tool Registration Summary ===")
    logger.info(f"Tools registered: {len(registered_tools)}/{total_configured}")
    logger.info(
        f"Success rate: {len(registered_tools) / total_configured:.1%}"
        if total_configured
        else "N/A"
    )

    logger.info("Registered tools:")
    for tool_name, description in sorted(registered_tools):
        # Truncate long descriptions for cleaner logs
        short_desc = description[:60] + "..." if len(description) > 60 else description
        logger.info(f"  ✓ {tool_name}: {short_desc}")

    logger.info(
        f"Lines of @srv.tool() decorators eliminated: {len(registered_tools) * 4}"
    )
    logger.info("=== Registration Complete ===")


def validate_tools_config(tools_config: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Validate tools configuration for bulk registration.

    Args:
        tools_config: Dictionary mapping tool names to their configuration

    Returns:
        Validation results with issues found

    Example:
        validation = validate_tools_config(tools_config)
        if not validation['valid']:
            print(f"Issues: {validation['issues']}")
    """
    issues = []
    valid_tools = 0

    for tool_name, config in tools_config.items():
        # Check required fields
        if "function" not in config and "use_case" not in config:
            issues.append(f"Tool '{tool_name}' missing 'function' or 'use_case' field")
            continue

        # Check function/use_case is callable
        function_or_use_case = config.get("function") or config.get("use_case")
        if not callable(function_or_use_case):
            issues.append(f"Tool '{tool_name}' function/use_case is not callable")
            continue

        # Check description exists
        if "description" not in config:
            issues.append(f"Tool '{tool_name}' missing 'description' field")
            # Don't fail for missing description, it's optional with default

        valid_tools += 1

    return {
        "valid": len(issues) == 0,
        "total_tools": len(tools_config),
        "valid_tools": valid_tools,
        "issues": issues,
    }


# Convenience function for the most common pattern
def register_tools(
    srv: FastMCP, tools_config: dict[str, dict[str, Any]]
) -> list[tuple[str, str]]:
    """
    Convenience function that automatically selects the appropriate registration method.

    This function examines the tools_config format and selects the most appropriate
    bulk registration method.

    Args:
        srv: FastMCP server instance to register tools with
        tools_config: Dictionary mapping tool names to their configuration

    Returns:
        List of tuples (tool_name, description) for registered tools
    """
    # Auto-detect configuration format
    if not tools_config:
        logger.warning("No tools configured for registration")
        return []

    # Check first tool config to determine format
    first_config = next(iter(tools_config.values()))

    if "function" in first_config:
        # Standard function format
        return bulk_register_tools(srv, tools_config)
    elif "use_case" in first_config:
        # Use case format - requires adapter
        from .adapters import create_mcp_adapter

        return bulk_register_with_adapter_pattern(srv, tools_config, create_mcp_adapter)
    else:
        raise BulkRegistrationError(
            "Unable to determine tools_config format - missing 'function' or 'use_case' keys"
        )


# ============================================================================
# Tool Removal Features (Phase 2 - v1.2.0)
# ============================================================================


def get_registered_tools(srv: FastMCP) -> list[str]:
    """
    Get list of all registered tool names from a FastMCP server.

    Args:
        srv: FastMCP server instance

    Returns:
        List of registered tool names

    Example:
        >>> tools = get_registered_tools(srv)
        >>> print(f"Server has {len(tools)} registered tools")
    """
    # Access internal _tool_manager to get tools synchronously
    # FastMCP v1.17.0+ has _tool_manager with _tools dict
    if hasattr(srv, "_tool_manager") and hasattr(srv._tool_manager, "_tools"):
        return list(srv._tool_manager._tools.keys())
    return []


def tool_exists(srv: FastMCP, tool_name: str) -> bool:
    """
    Check if a tool is registered on the server.

    Args:
        srv: FastMCP server instance
        tool_name: Name of tool to check

    Returns:
        True if tool exists, False otherwise

    Example:
        >>> if tool_exists(srv, "get_weather"):
        ...     print("Weather tool is available")
    """
    return tool_name in get_registered_tools(srv)


def count_tools(srv: FastMCP) -> int:
    """
    Count the number of registered tools on the server.

    Args:
        srv: FastMCP server instance

    Returns:
        Number of registered tools

    Example:
        >>> print(f"Server has {count_tools(srv)} tools")
    """
    return len(get_registered_tools(srv))


def bulk_remove_tools(srv: FastMCP, tool_names: list[str]) -> dict[str, Any]:
    """
    Remove multiple tools from a running MCP server.

    Uses the FastMCP.remove_tool() method introduced in MCP SDK v1.17.0.
    Provides detailed reporting of successful and failed removals.

    Args:
        srv: FastMCP server instance
        tool_names: List of tool names to remove

    Returns:
        Dictionary containing:
        - removed: List of successfully removed tool names
        - failed: List of (tool_name, error_message) tuples
        - success_rate: Float percentage (0.0-100.0)

    Example:
        >>> result = bulk_remove_tools(srv, ["tool1", "tool2", "tool3"])
        >>> print(f"Removed {len(result['removed'])} tools")
        >>> print(f"Success rate: {result['success_rate']:.1f}%")
    """
    logger.info(f"Starting bulk removal of {len(tool_names)} tools...")

    removed = []
    failed = []

    for tool_name in tool_names:
        try:
            srv.remove_tool(tool_name)
            removed.append(tool_name)
            logger.debug(f"Successfully removed tool: {tool_name}")
        except Exception as e:
            error_msg = str(e)
            failed.append((tool_name, error_msg))
            logger.warning(f"Failed to remove tool '{tool_name}': {error_msg}")

    total = len(tool_names)
    success_rate = (len(removed) / total * 100) if total > 0 else 0.0

    logger.info(
        f"Bulk removal complete: {len(removed)}/{total} tools removed "
        f"({success_rate:.1f}% success rate)"
    )

    return {
        "removed": removed,
        "failed": failed,
        "success_rate": success_rate,
    }


def bulk_replace_tools(
    srv: FastMCP,
    tools_to_remove: list[str],
    tools_to_add: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Atomically replace tools - remove old ones and add new ones.

    This function performs a two-phase operation:
    1. Remove specified tools
    2. Add new tools using bulk_register_tools

    If addition fails, the function reports the failure but does not
    automatically rollback removals (as the original tool configurations
    are not stored).

    Args:
        srv: FastMCP server instance
        tools_to_remove: List of tool names to remove
        tools_to_add: Dictionary of tools to add (same format as bulk_register_tools)

    Returns:
        Dictionary containing:
        - removed: List of successfully removed tool names
        - added: List of successfully added tool names
        - removal_failed: List of (tool_name, error) tuples for failed removals
        - addition_failed: Boolean indicating if addition phase failed
        - errors: List of error messages if any

    Example:
        >>> result = bulk_replace_tools(
        ...     srv,
        ...     ["old_tool1", "old_tool2"],
        ...     {"new_tool1": {"function": fn1, "description": "New tool 1"}}
        ... )
        >>> print(f"Replaced {len(result['removed'])} tools with {len(result['added'])}")
    """
    logger.info(
        f"Starting bulk replacement: removing {len(tools_to_remove)} tools, "
        f"adding {len(tools_to_add)} tools"
    )

    errors = []
    added = []
    addition_failed = False

    # Phase 1: Remove old tools
    removal_result = bulk_remove_tools(srv, tools_to_remove)
    removed = removal_result["removed"]
    removal_failed = removal_result["failed"]

    if removal_failed:
        errors.extend(
            [f"Remove failed for '{name}': {err}" for name, err in removal_failed]
        )

    # Phase 2: Add new tools
    try:
        addition_result = bulk_register_tools(srv, tools_to_add)
        added = [name for name, _ in addition_result]
        logger.info(f"Successfully added {len(added)} new tools")
    except BulkRegistrationError as e:
        addition_failed = True
        errors.append(f"Addition phase failed: {str(e)}")
        logger.error(f"Addition phase failed: {str(e)}")

    logger.info(
        f"Bulk replacement complete: removed {len(removed)}, added {len(added)}, "
        f"{len(errors)} errors"
    )

    return {
        "removed": removed,
        "added": added,
        "removal_failed": removal_failed,
        "addition_failed": addition_failed,
        "errors": errors,
    }


def conditional_remove_tools(
    srv: FastMCP, condition: Callable[[str], bool]
) -> list[str]:
    """
    Remove tools matching a condition predicate.

    This function retrieves all registered tools, applies the condition
    function to each tool name, and removes tools where the condition
    returns True.

    Args:
        srv: FastMCP server instance
        condition: Callable that takes tool name and returns True to remove

    Returns:
        List of removed tool names

    Example:
        >>> # Remove all deprecated tools
        >>> removed = conditional_remove_tools(
        ...     srv,
        ...     lambda name: "deprecated" in name.lower()
        ... )
        >>> print(f"Removed {len(removed)} deprecated tools")

        >>> # Remove tools by prefix
        >>> removed = conditional_remove_tools(
        ...     srv,
        ...     lambda name: name.startswith("test_")
        ... )
    """
    logger.info("Starting conditional tool removal...")

    # Get all registered tools
    all_tools = get_registered_tools(srv)
    logger.debug(f"Found {len(all_tools)} registered tools")

    # Filter tools matching condition
    tools_to_remove = [name for name in all_tools if condition(name)]
    logger.info(f"Condition matched {len(tools_to_remove)} tools for removal")

    if not tools_to_remove:
        logger.info("No tools matched the removal condition")
        return []

    # Remove matching tools
    result = bulk_remove_tools(srv, tools_to_remove)
    removed = result["removed"]

    if result["failed"]:
        logger.warning(f"Failed to remove {len(result['failed'])} tools")

    logger.info(f"Conditional removal complete: {len(removed)} tools removed")
    return removed
