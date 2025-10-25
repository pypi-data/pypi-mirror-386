"""MCP server for Maxwell workflows.

Exposes all registered Maxwell workflows as MCP tools with auto-generated schemas
from workflow metadata and docstrings.

Usage:
    # Stdio mode (for Claude Desktop):
    python -m maxwell.mcp_server

    # Or as module:
    from maxwell.mcp_server import create_server
    server = create_server()
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from maxwell.api import execute_workflow, list_workflows, workflow_result_to_dict

logger = logging.getLogger(__name__)

__all__ = ["create_server", "main"]


def create_server() -> Server:
    """Create and configure MCP server with all Maxwell workflows as tools.

    Returns:
        Configured MCP Server instance

    """
    server = Server("maxwell")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available Maxwell workflows as MCP tools."""
        tools = []

        for workflow_meta in list_workflows():
            # Build parameter schema from workflow CLI parameters
            properties = {}
            required = []

            # Add project_root parameter (optional for all workflows)
            properties["project_root"] = {
                "type": "string",
                "description": "Project root directory (defaults to current directory)",
            }

            # Add workflow-specific parameters
            for param in workflow_meta.parameters:
                param_name = param["name"]
                param_type = param.get("type", str).__name__

                # Map Python types to JSON schema types
                json_type = {
                    "str": "string",
                    "int": "number",
                    "float": "number",
                    "bool": "boolean",
                }.get(param_type, "string")

                properties[param_name] = {
                    "type": json_type,
                    "description": param.get("help", f"Parameter: {param_name}"),
                }

                # Add default if specified
                if "default" in param:
                    properties[param_name]["default"] = param["default"]

                # Mark as required if specified
                if param.get("required", False):
                    required.append(param_name)

            # Create tool schema
            tool = Tool(
                name=f"maxwell_{workflow_meta.workflow_id.replace('-', '_')}",
                description=(
                    f"{workflow_meta.name}: {workflow_meta.description}\n\n"
                    f"Category: {workflow_meta.category}\n"
                    f"Tags: {', '.join(workflow_meta.tags)}\n"
                    f"Version: {workflow_meta.version}"
                ),
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            )

            tools.append(tool)

        logger.info(f"Registered {len(tools)} Maxwell workflows as MCP tools")
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Execute a Maxwell workflow tool.

        Args:
            name: Tool name (maxwell_{workflow_id})
            arguments: Tool arguments including project_root and workflow parameters

        Returns:
            List of TextContent with workflow results

        """
        # Extract workflow ID from tool name
        if not name.startswith("maxwell_"):
            return [
                TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'. All Maxwell tools start with 'maxwell_'",
                )
            ]

        workflow_id = name[8:].replace("_", "-")  # Remove 'maxwell_' prefix and convert underscores

        # Extract parameters
        project_root_str = arguments.get("project_root")
        project_root = Path(project_root_str) if project_root_str else Path.cwd()

        # Build context from remaining arguments
        context = {k: v for k, v in arguments.items() if k != "project_root"}

        logger.info(f"Executing workflow {workflow_id} with context: {context}")

        try:
            # Execute workflow
            result = execute_workflow(workflow_id, project_root, context)

            # Convert result to dict
            result_dict = workflow_result_to_dict(result)

            # Format response based on status
            if result.status.value == "completed":
                # Success - return formatted results
                response_parts = [
                    f"[OK] {workflow_id} completed successfully\n",
                    "\n**Metrics:**",
                    f"- Files processed: {result.metrics.files_processed}",
                    (
                        f"- Execution time: {result.metrics.execution_time_seconds:.2f}s"
                        if result.metrics.execution_time_seconds
                        else ""
                    ),
                ]

                # Add custom metrics if present
                if result.metrics.custom_metrics:
                    response_parts.append("\n**Details:**")
                    for key, value in result.metrics.custom_metrics.items():
                        response_parts.append(f"- {key}: {value}")

                # Add artifacts summary if present
                if result.artifacts:
                    response_parts.append(f"\n**Artifacts:** {', '.join(result.artifacts.keys())}")

                # Add formatted output if present (for validate workflow, etc.)
                if "formatted_output" in result.artifacts:
                    response_parts.append(f"\n\n{result.artifacts['formatted_output']}")

                response_text = "\n".join(filter(None, response_parts))

            elif result.status.value == "failed":
                # Failure - return error
                response_text = (
                    f"[FAILED] {workflow_id} failed\n\n"
                    f"**Error:** {result.error_message}\n\n"
                    f"Check logs for more details."
                )

            else:
                # Other status - return generic info
                response_text = (
                    f"Workflow {workflow_id} finished with status: {result.status.value}\n"
                    f"See full result for details."
                )

            # Return both formatted text and full JSON result
            return [
                TextContent(type="text", text=response_text),
                TextContent(
                    type="text", text=f"\n\n**Full Result (JSON):**\n```json\n{result_dict}\n```"
                ),
            ]

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text", text=f"[ERROR] Error executing workflow {workflow_id}: {str(e)}"
                )
            ]

    return server


async def main():
    """Run MCP server in stdio mode."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting Maxwell MCP server...")

    # Create and run server
    server = create_server()

    # Run stdio server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Maxwell MCP server running on stdio")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
