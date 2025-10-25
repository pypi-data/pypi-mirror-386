"""Factory functions for creating tools from agent resources."""

from __future__ import annotations

from langchain_core.tools import BaseTool, StructuredTool
from uipath.agent.models.agent import (
    AgentContextResourceConfig,
    AgentProcessToolResourceConfig,
    BaseAgentResourceConfig,
    LowCodeAgentDefinition,
)

from .context_tool import create_context_tool
from .process_tool import create_process_tool


async def create_tools_from_resources(
    agent: LowCodeAgentDefinition,
) -> list[BaseTool]:
    tools: list[BaseTool] = []

    for resource in agent.resources:
        tool = await _build_tool_for_resource(resource)
        if tool is not None:
            tools.append(tool)

    return tools


async def _build_tool_for_resource(
    resource: BaseAgentResourceConfig,
) -> StructuredTool | None:
    if isinstance(resource, AgentProcessToolResourceConfig):
        return create_process_tool(resource)

    elif isinstance(resource, AgentContextResourceConfig):
        return create_context_tool(resource)

    return None
