import logging
from typing import Any, Optional, cast

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from uipath._cli._runtime._contracts import (
    UiPathApiTrigger,
    UiPathErrorCategory,
    UiPathResumeTrigger,
    UiPathResumeTriggerType,
)
from uipath._cli._runtime._hitl import HitlReader

from ._context import LangGraphRuntimeContext
from ._conversation import uipath_to_human_messages
from ._exception import LangGraphRuntimeError

logger = logging.getLogger(__name__)


async def get_graph_input(
    context: LangGraphRuntimeContext,
    memory: AsyncSqliteSaver,
    resume_triggers_table: str = "__uipath_resume_triggers",
) -> Any:
    """
    Process the input data for graph execution, handling both fresh starts and resume scenarios.

    This method determines whether the graph is being executed fresh or resumed from a previous state.
    For fresh executions, it returns the input JSON directly. For resume scenarios, it fetches
    the latest trigger information from the database and constructs a Command object with the
    appropriate resume data.

    The method handles different types of resume triggers:
    - API triggers: Creates an UiPathApiTrigger with inbox_id and request payload
    - Other triggers: Uses the HitlReader to process the resume data

    Args:
        context: The runtime context for the graph execution.
        memory: AsyncSqliteSaver. The async database saver used to fetch resume trigger data.
        resume_triggers_table: str, optional. The name of the database table containing resume triggers (default: "__uipath_resume_triggers").

    Returns:
        Any: For fresh executions, returns the input JSON data directly.
             For resume scenarios, returns a Command object containing the resume data
             processed through the appropriate trigger handler.

    Raises:
        LangGraphRuntimeError: If there's an error fetching trigger data from the database
            during resume processing.
    """
    logger.debug(f"Resumed: {context.resume} Input: {context.input_json}")

    # Fresh execution - return input directly
    if not context.resume:
        if context.input_message:
            return {"messages": uipath_to_human_messages(context.input_message)}
        return context.input_json

    # Resume with explicit input provided
    if context.input_json:
        return Command(resume=context.input_json)

    # Resume from database trigger
    trigger = await _get_latest_trigger(
        memory, resume_triggers_table=resume_triggers_table
    )
    if not trigger:
        return Command(resume=context.input_json)

    trigger_type, key, folder_path, folder_key, payload = trigger
    resume_trigger = UiPathResumeTrigger(
        trigger_type=trigger_type,
        item_key=key,
        folder_path=folder_path,
        folder_key=folder_key,
        payload=payload,
    )
    logger.debug(f"ResumeTrigger: {trigger_type} {key}")

    # Populate back expected fields for api_triggers
    if resume_trigger.trigger_type == UiPathResumeTriggerType.API:
        resume_trigger.api_resume = UiPathApiTrigger(
            inbox_id=resume_trigger.item_key, request=resume_trigger.payload
        )

    return Command(resume=await HitlReader.read(resume_trigger))


async def _get_latest_trigger(
    memory: AsyncSqliteSaver,
    resume_triggers_table: str = "__uipath_resume_triggers",
) -> Optional[tuple[str, str, str, str, str]]:
    """
    Fetch the most recent resume trigger from the database.

    This private method queries the resume triggers table to retrieve the latest trigger
    information based on timestamp. It handles database connection setup and executes
    a SQL query to fetch trigger data needed for resume operations.

    The method returns trigger information as a tuple containing:
    - type: The type of trigger (e.g., 'API', 'MANUAL', etc.)
    - key: The unique identifier for the trigger/item
    - folder_path: The path to the folder containing the trigger
    - folder_key: The unique identifier for the folder
    - payload: The serialized payload data associated with the trigger

    Args:
        memory: The AsyncSqliteSaver instance used to access the database.
        resume_triggers_table: The name of the table containing resume triggers (default: "__uipath_resume_triggers").

    Returns:
        Optional[tuple[str, str, str, str, str]]: A tuple containing (type, key, folder_path,
            folder_key, payload) for the most recent trigger, or None if no triggers are found
            or if the memory context is not available.

    Raises:
        LangGraphRuntimeError: If there's an error during database connection setup, query
            execution, or result fetching. The original exception is wrapped with context
            about the database operation failure.
    """
    if memory is None:
        return None

    try:
        await memory.setup()
        async with (
            memory.lock,
            memory.conn.cursor() as cur,
        ):
            await cur.execute(f"""
                SELECT type, key, folder_path, folder_key, payload
                FROM {resume_triggers_table}
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            result = await cur.fetchone()
            if result is None:
                return None
            return cast(tuple[str, str, str, str, str], tuple(result))
    except Exception as e:
        raise LangGraphRuntimeError(
            "DB_QUERY_FAILED",
            "Database query failed",
            f"Error querying resume trigger information: {str(e)}",
            UiPathErrorCategory.SYSTEM,
        ) from e
