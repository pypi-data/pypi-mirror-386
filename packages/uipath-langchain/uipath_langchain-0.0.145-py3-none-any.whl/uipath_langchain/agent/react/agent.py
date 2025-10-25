import os
from typing import Sequence, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from pydantic import BaseModel

from ..tools import create_tool_node
from .init_node import (
    create_init_node,
)
from .llm_node import (
    create_llm_node,
)
from .router import (
    route_agent,
)
from .state import AgentGraphNode, AgentGraphState
from .terminate_node import (
    create_terminate_node,
)
from .tools import create_flow_control_tools


def create_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    messages: Sequence[SystemMessage | HumanMessage],
    *,
    state_schema: Type[AgentGraphState] = AgentGraphState,
    response_format: type[BaseModel] | None = None,
    recursion_limit: int = 50,
) -> StateGraph[AgentGraphState]:
    """Build agent graph with INIT -> AGENT <-> TOOLS loop, terminated by control flow tools.

    Control flow tools (end_execution, raise_error) are auto-injected alongside regular tools.
    """
    os.environ["LANGCHAIN_RECURSION_LIMIT"] = str(recursion_limit)

    agent_tools = list(tools)
    flow_control_tools: list[BaseTool] = create_flow_control_tools(response_format)
    llm_tools: list[BaseTool] = [*agent_tools, *flow_control_tools]

    init_node = create_init_node(messages)
    agent_node = create_llm_node(model, llm_tools)
    tool_nodes = create_tool_node(agent_tools)
    terminate_node = create_terminate_node(response_format)

    builder: StateGraph[AgentGraphState] = StateGraph(state_schema)
    builder.add_node(AgentGraphNode.INIT, init_node)
    builder.add_node(AgentGraphNode.AGENT, agent_node)

    for tool_name, tool_node in tool_nodes.items():
        builder.add_node(tool_name, tool_node)

    builder.add_node(AgentGraphNode.TERMINATE, terminate_node)

    builder.add_edge(START, AgentGraphNode.INIT)
    builder.add_edge(AgentGraphNode.INIT, AgentGraphNode.AGENT)

    tool_node_names = list(tool_nodes.keys())
    builder.add_conditional_edges(
        AgentGraphNode.AGENT,
        route_agent,
        [AgentGraphNode.AGENT, *tool_node_names, AgentGraphNode.TERMINATE],
    )

    for tool_name in tool_node_names:
        builder.add_edge(tool_name, AgentGraphNode.AGENT)

    builder.add_edge(AgentGraphNode.TERMINATE, END)

    return builder
