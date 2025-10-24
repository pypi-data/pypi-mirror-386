"""MCP Server implementation"""

import asyncio
import logging
import sys
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import CloudTruthClient
from .config import ConfigManager
from .errors import sanitize_error_message
from .models import ServerConfig
from .tools import ToolsHandler

logger = logging.getLogger(__name__)


class CloudTruthMCPServer:
    """CloudTruth MCP Server"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.ct_client = CloudTruthClient(config)
        self.tools_handler = ToolsHandler(self.ct_client, config)
        self.server = Server("cloudtruth-mcp-server")

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="list_projects",
                    description="List all accessible CloudTruth projects",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name_filter": {
                                "type": "string",
                                "description": "Optional filter for project names (case-insensitive)",
                            }
                        },
                    },
                ),
                Tool(
                    name="create_project",
                    description="Create a new CloudTruth project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the new project (required)",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the project (optional)",
                            },
                            "parent_project": {
                                "type": "string",
                                "description": "Parent project name or ID for inheritance (optional)",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="delete_project",
                    description="Delete a CloudTruth project (requires empty project by default for safety)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID to delete (required)",
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force deletion even if project contains parameters (default: false)",
                                "default": False,
                            },
                        },
                        "required": ["project"],
                    },
                ),
                Tool(
                    name="list_environments",
                    description="List all CloudTruth environments with hierarchy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name_filter": {
                                "type": "string",
                                "description": "Optional filter for environment names",
                            }
                        },
                    },
                ),
                Tool(
                    name="create_environment",
                    description="Create a new CloudTruth environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the new environment (required)",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the environment (optional)",
                            },
                            "parent_environment": {
                                "type": "string",
                                "description": "Parent environment name or ID for hierarchy (optional)",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="get_parameter",
                    description="Retrieve a single parameter value from CloudTruth",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "parameter_name": {
                                "type": "string",
                                "description": "Name of the parameter to retrieve",
                            },
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID (optional, uses default if not specified)",
                            },
                            "include_secrets": {
                                "type": "boolean",
                                "description": "Set to true to include unmasked secret values (default: false)",
                                "default": False,
                            },
                            "as_of": {
                                "type": "string",
                                "description": "Point-in-time query: tag name or ISO 8601 timestamp (optional)",
                            },
                        },
                        "required": ["project", "parameter_name"],
                    },
                ),
                Tool(
                    name="get_parameters",
                    description="Retrieve all parameters for a project in a specific environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID (optional, uses default if not specified)",
                            },
                            "include_secrets": {
                                "type": "boolean",
                                "description": "Set to true to include unmasked secret values (default: false)",
                                "default": False,
                            },
                            "name_prefix": {
                                "type": "string",
                                "description": "Filter parameters by name prefix (e.g., 'DB_' for database params)",
                            },
                            "as_of": {
                                "type": "string",
                                "description": "Point-in-time query: tag name or ISO 8601 timestamp (optional)",
                            },
                        },
                        "required": ["project"],
                    },
                ),
                Tool(
                    name="set_parameter",
                    description="Set or update a parameter value in CloudTruth",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "parameter_name": {
                                "type": "string",
                                "description": "Name of the parameter to set",
                            },
                            "value": {
                                "type": "string",
                                "description": "The value to set",
                            },
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID (optional, uses default if not specified)",
                            },
                            "secret": {
                                "type": "boolean",
                                "description": "Mark this parameter as secret (default: false)",
                                "default": False,
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the parameter (only used if creating new parameter)",
                            },
                        },
                        "required": ["project", "parameter_name", "value"],
                    },
                ),
                Tool(
                    name="create_parameter",
                    description="Create a new parameter definition in a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "parameter_name": {
                                "type": "string",
                                "description": "Name of the parameter (must not start with 'cloudtruth.')",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the parameter",
                            },
                            "secret": {
                                "type": "boolean",
                                "description": "Mark this parameter as secret (default: false)",
                                "default": False,
                            },
                            "parameter_type": {
                                "type": "string",
                                "description": "Parameter type (default: 'string')",
                                "enum": ["string", "integer", "boolean"],
                                "default": "string",
                            },
                        },
                        "required": ["project", "parameter_name"],
                    },
                ),
                Tool(
                    name="delete_parameter",
                    description="Delete a parameter from a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "parameter_name": {
                                "type": "string",
                                "description": "Name of the parameter to delete",
                            },
                        },
                        "required": ["project", "parameter_name"],
                    },
                ),
                Tool(
                    name="preview_template",
                    description="Preview template rendering with parameter substitution",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "template_body": {
                                "type": "string",
                                "description": "Template body with {{PARAM}} placeholders",
                            },
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID (optional, uses default if not specified)",
                            },
                            "as_of": {
                                "type": "string",
                                "description": "Point-in-time query: tag name or ISO 8601 timestamp (optional)",
                            },
                        },
                        "required": ["project", "template_body"],
                    },
                ),
                Tool(
                    name="create_tag",
                    description="Create a point-in-time snapshot tag for an environment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID",
                            },
                            "tag_name": {
                                "type": "string",
                                "description": "Name for the tag",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the tag",
                            },
                        },
                        "required": ["environment", "tag_name"],
                    },
                ),
                Tool(
                    name="export_parameters",
                    description="Export parameters in various formats (JSON, dotenv, YAML)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name or ID",
                            },
                            "environment": {
                                "type": "string",
                                "description": "Environment name or ID (optional, uses default if not specified)",
                            },
                            "format": {
                                "type": "string",
                                "description": "Export format (default: json)",
                                "enum": ["json", "dotenv", "env", "yaml"],
                                "default": "json",
                            },
                            "include_secrets": {
                                "type": "boolean",
                                "description": "Set to true to include unmasked secret values (default: false)",
                                "default": False,
                            },
                            "name_prefix": {
                                "type": "string",
                                "description": "Filter parameters by name prefix",
                            },
                        },
                        "required": ["project"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
            """Execute tool"""
            try:
                logger.info(f"Tool called: {name}")

                # Route to appropriate handler
                if name == "list_projects":
                    result = await self.tools_handler.list_projects(
                        name_filter=arguments.get("name_filter")
                    )
                elif name == "create_project":
                    result = await self.tools_handler.create_project(**arguments)
                elif name == "delete_project":
                    result = await self.tools_handler.delete_project(**arguments)
                elif name == "list_environments":
                    result = await self.tools_handler.list_environments(
                        name_filter=arguments.get("name_filter")
                    )
                elif name == "create_environment":
                    result = await self.tools_handler.create_environment(**arguments)
                elif name == "get_parameter":
                    result = await self.tools_handler.get_parameter(**arguments)
                elif name == "get_parameters":
                    result = await self.tools_handler.get_parameters(**arguments)
                elif name == "set_parameter":
                    result = await self.tools_handler.set_parameter(**arguments)
                elif name == "create_parameter":
                    result = await self.tools_handler.create_parameter(**arguments)
                elif name == "delete_parameter":
                    result = await self.tools_handler.delete_parameter(**arguments)
                elif name == "preview_template":
                    result = await self.tools_handler.preview_template(**arguments)
                elif name == "create_tag":
                    result = await self.tools_handler.create_tag(**arguments)
                elif name == "export_parameters":
                    result = await self.tools_handler.export_parameters(**arguments)
                else:
                    result = f"Unknown tool: {name}"
                    logger.error(result)

                return [TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Tool execution error: {sanitize_error_message(str(e))}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=error_msg)]

    async def run(self) -> None:
        """Run the server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.ct_client.close()


def main() -> None:
    """Main entry point"""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load()

        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,  # Log to stderr to avoid interfering with stdio transport
        )

        logger.info("CloudTruth MCP Server starting...")
        logger.info(f"API Base URL: {config.api_base_url}")
        logger.info(f"Default Project: {config.default_project or 'None'}")
        logger.info(f"Default Environment: {config.default_environment or 'None'}")

        # Run server
        server = CloudTruthMCPServer(config)

        try:
            asyncio.run(server.run())
        finally:
            asyncio.run(server.cleanup())

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {sanitize_error_message(str(e))}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
