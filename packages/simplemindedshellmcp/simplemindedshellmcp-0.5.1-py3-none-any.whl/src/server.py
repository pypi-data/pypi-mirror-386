#!/usr/bin/env python3
"""Simpleminded Shell MCP Server

Provides resources and tools for AI assistants to understand and work
with simpleminded-shell environments.
"""

import json
import logging
from typing import Any, Dict
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .config_parser import ShellConfigParser
from .alias_detector import AliasDetector
from .command_translator import CommandTranslator
from .tool_checker import ToolChecker
from .example_provider import ExampleProvider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("simpleminded-shell")

# Initialize components
config_parser = ShellConfigParser()
tool_checker = ToolChecker()
translator = CommandTranslator()
example_provider = ExampleProvider()

# Initialize alias detector if config is available
alias_detector = None
if config_parser.config_path:
    alias_detector = AliasDetector(config_parser.get_raw_config())


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    resources = [
        Resource(
            uri="simpleminded://config/info",
            name="Configuration Info",
            description="Information about the detected shell configuration",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://aliases/all",
            name="All Aliases",
            description="Complete list of all shell aliases",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://aliases/categories",
            name="Alias Categories",
            description="Aliases organized by category (file, git, docker, etc.)",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://tools/status",
            name="Tool Installation Status",
            description="Check which simpleminded-shell tools are installed",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://tools/summary",
            name="Tool Summary",
            description="Summary of installed vs missing tools",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://examples/all",
            name="All Examples",
            description="Usage examples for all tools",
            mimeType="application/json",
        ),
        Resource(
            uri="simpleminded://workflows/all",
            name="Common Workflows",
            description="Multi-step workflows using simpleminded-shell tools",
            mimeType="application/json",
        ),
    ]

    # Add category-specific resources if aliases are available
    if alias_detector:
        for category in alias_detector.get_all_categories():
            resources.append(
                Resource(
                    uri=f"simpleminded://aliases/category/{category}",
                    name=f"{category.title()} Aliases",
                    description=f"Aliases in the {category} category",
                    mimeType="application/json",
                )
            )

    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific resource."""
    logger.info(f"Reading resource: {uri}")

    if uri == "simpleminded://config/info":
        return json.dumps(config_parser.get_config_info(), indent=2)

    elif uri == "simpleminded://aliases/all":
        if not alias_detector:
            return json.dumps({"error": "No simpleminded-shell configuration detected"})
        return json.dumps(alias_detector.to_dict(), indent=2)

    elif uri == "simpleminded://aliases/categories":
        if not alias_detector:
            return json.dumps({"error": "No simpleminded-shell configuration detected"})
        categories = {}
        for category in alias_detector.get_all_categories():
            categories[category] = {
                name: {"command": alias.command}
                for name, alias in alias_detector.get_aliases_by_category(category).items()
            }
        return json.dumps(categories, indent=2)

    elif uri.startswith("simpleminded://aliases/category/"):
        category = uri.split("/")[-1]
        if not alias_detector:
            return json.dumps({"error": "No simpleminded-shell configuration detected"})
        aliases = alias_detector.get_aliases_by_category(category)
        result = {
            name: {"command": alias.command, "category": alias.category}
            for name, alias in aliases.items()
        }
        return json.dumps(result, indent=2)

    elif uri == "simpleminded://tools/status":
        all_tools = tool_checker.check_all_tools()
        result = {
            name: {
                "installed": info.installed,
                "version": info.version,
                "path": info.path,
                "brew_package": info.brew_package,
            }
            for name, info in all_tools.items()
        }
        return json.dumps(result, indent=2)

    elif uri == "simpleminded://tools/summary":
        return json.dumps(tool_checker.get_summary(), indent=2)

    elif uri == "simpleminded://examples/all":
        examples = {}
        for tool in example_provider.get_all_tools():
            examples[tool] = example_provider.get_examples(tool)
        return json.dumps(examples, indent=2)

    elif uri == "simpleminded://workflows/all":
        return json.dumps(example_provider.get_all_workflows(), indent=2)

    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="translate_command",
            description="Translate traditional Unix command to modern simpleminded-shell equivalent",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The traditional Unix command to translate (e.g., 'grep -r pattern')",
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="check_tool",
            description="Check if a specific tool is installed and get version information",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to check (e.g., 'bat', 'fd', 'rg')",
                    },
                },
                "required": ["tool_name"],
            },
        ),
        Tool(
            name="get_examples",
            description="Get usage examples for a tool or use case",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool name (e.g., 'bat', 'fd', 'rg')",
                    },
                    "use_case": {
                        "type": "string",
                        "description": "Optional specific use case to filter examples",
                    },
                },
                "required": ["tool"],
            },
        ),
        Tool(
            name="explain_alias",
            description="Explain what a shell alias actually does",
            inputSchema={
                "type": "object",
                "properties": {
                    "alias_name": {
                        "type": "string",
                        "description": "Name of the alias to explain",
                    },
                },
                "required": ["alias_name"],
            },
        ),
        Tool(
            name="search_examples",
            description="Search for examples by keyword or description",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'find python files', 'case insensitive')",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_tool_benefits",
            description="Get benefits of using a modern tool over traditional alternatives",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool name (e.g., 'bat', 'fd', 'rg', 'eza')",
                    },
                },
                "required": ["tool"],
            },
        ),
        Tool(
            name="recommend_tools",
            description="Get tool recommendations based on a task description",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Description of what you want to do (e.g., 'search for text in files')",
                    },
                },
                "required": ["task"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        if name == "translate_command":
            command = arguments.get("command", "")
            translation = translator.translate(command)

            if translation:
                result = {
                    "original": translation.original,
                    "modern": translation.modern,
                    "explanation": translation.explanation,
                    "tool": translation.tool,
                }
            else:
                result = {
                    "error": "Could not translate command",
                    "original": command,
                    "suggestion": "Command may already use modern tools or pattern not recognized",
                }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "check_tool":
            tool_name = arguments.get("tool_name", "")
            info = tool_checker.check_tool(tool_name)

            result = {
                "name": info.name,
                "installed": info.installed,
                "version": info.version,
                "path": info.path,
                "install_command": tool_checker.get_installation_command(tool_name),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_examples":
            tool = arguments.get("tool", "")
            use_case = arguments.get("use_case")

            examples = example_provider.get_examples(tool, use_case)

            if not examples:
                result = {"error": f"No examples found for tool: {tool}"}
            else:
                result = {"tool": tool, "examples": examples}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "explain_alias":
            alias_name = arguments.get("alias_name", "")

            if not alias_detector:
                result = {"error": "No simpleminded-shell configuration detected"}
            else:
                alias = alias_detector.get_alias(alias_name)
                if alias:
                    result = {
                        "alias": alias_name,
                        "command": alias.command,
                        "category": alias.category,
                        "explanation": translator.explain_alias(alias_name, alias.command),
                    }
                else:
                    result = {"error": f"Alias not found: {alias_name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_examples":
            query = arguments.get("query", "")
            results = example_provider.search_examples(query)

            result = {
                "query": query,
                "matches": len(results),
                "examples": results,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_tool_benefits":
            tool = arguments.get("tool", "")
            benefits = translator.get_tool_benefits(tool)

            result = {
                "tool": tool,
                "benefits": benefits,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "recommend_tools":
            task = arguments.get("task", "")
            recommendations = example_provider.get_recommendations(task)

            result = {
                "task": task,
                "recommendations": recommendations,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def async_main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Simpleminded Shell MCP Server starting...")
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
