"""ReAct Agent loop utilities."""

from typing import Any, Sequence

from jsonschema_pydantic import jsonschema_to_pydantic  # type: ignore[import-untyped]
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel
from uipath.agent.react import END_EXECUTION_TOOL


def resolve_output_model(
    output_schema: dict[str, Any] | None,
) -> type[BaseModel]:
    """Fallback to default end_execution tool schema when no agent output schema is provided."""
    if output_schema:
        return jsonschema_to_pydantic(output_schema)

    return END_EXECUTION_TOOL.args_schema


def count_successive_completions(messages: Sequence[BaseMessage]) -> int:
    """Count consecutive AIMessages without tool calls at end of message history."""
    if not messages:
        return 0

    count = 0
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            break

        if message.tool_calls:
            break

        if not message.content:
            break

        count += 1

    return count
