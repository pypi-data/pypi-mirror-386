import asyncio
from typing import List, Optional

from openinference.instrumentation.langchain import (
    LangChainInstrumentor,
    get_current_span,
)
from uipath._cli._evals._console_progress_reporter import ConsoleProgressReporter
from uipath._cli._evals._progress_reporter import StudioWebProgressReporter
from uipath._cli._evals._runtime import UiPathEvalContext, UiPathEvalRuntime
from uipath._cli._runtime._contracts import (
    UiPathRuntimeFactory,
)
from uipath._cli._utils._eval_set import EvalHelpers
from uipath._cli.middlewares import MiddlewareResult
from uipath._events._event_bus import EventBus
from uipath.eval._helpers import auto_discover_entrypoint
from uipath.tracing import LlmOpsHttpExporter

from uipath_langchain._cli._runtime._context import LangGraphRuntimeContext
from uipath_langchain._cli._runtime._runtime import LangGraphScriptRuntime
from uipath_langchain._cli._utils._graph import LangGraphConfig
from uipath_langchain._tracing import (
    _instrument_traceable_attributes,
)


def langgraph_eval_middleware(
    entrypoint: Optional[str], eval_set: Optional[str], eval_ids: List[str], **kwargs
) -> MiddlewareResult:
    config = LangGraphConfig()
    if not config.exists:
        return MiddlewareResult(
            should_continue=True
        )  # Continue with normal flow if no langgraph.json

    try:
        _instrument_traceable_attributes()

        event_bus = EventBus()

        if kwargs.get("register_progress_reporter", False):
            progress_reporter = StudioWebProgressReporter(
                spans_exporter=LlmOpsHttpExporter(extra_process_spans=True)
            )
            asyncio.run(progress_reporter.subscribe_to_eval_runtime_events(event_bus))
        console_reporter = ConsoleProgressReporter()
        asyncio.run(console_reporter.subscribe_to_eval_runtime_events(event_bus))

        def generate_runtime_context(
            context_entrypoint: str, **context_kwargs
        ) -> LangGraphRuntimeContext:
            context = LangGraphRuntimeContext.with_defaults(**context_kwargs)
            context.entrypoint = context_entrypoint
            return context

        runtime_entrypoint = entrypoint or auto_discover_entrypoint()

        eval_context = UiPathEvalContext.with_defaults(
            entrypoint=runtime_entrypoint, **kwargs
        )
        eval_context.eval_set = eval_set or EvalHelpers.auto_discover_eval_set()
        eval_context.eval_ids = eval_ids

        def generate_runtime(ctx: LangGraphRuntimeContext) -> LangGraphScriptRuntime:
            return LangGraphScriptRuntime(ctx, ctx.entrypoint)

        runtime_factory = UiPathRuntimeFactory(
            LangGraphScriptRuntime,
            LangGraphRuntimeContext,
            context_generator=lambda **context_kwargs: generate_runtime_context(
                context_entrypoint=runtime_entrypoint,
                **context_kwargs,
            ),
            runtime_generator=generate_runtime,
        )

        if eval_context.job_id:
            runtime_factory.add_span_exporter(
                LlmOpsHttpExporter(extra_process_spans=True)
            )

        runtime_factory.add_instrumentor(LangChainInstrumentor, get_current_span)

        async def execute():
            async with UiPathEvalRuntime.from_eval_context(
                factory=runtime_factory, context=eval_context, event_bus=event_bus
            ) as eval_runtime:
                await eval_runtime.execute()
                await event_bus.wait_for_all()

        asyncio.run(execute())
        return MiddlewareResult(should_continue=False)

    except Exception as e:
        return MiddlewareResult(
            should_continue=False, error_message=f"Error running evaluation: {str(e)}"
        )
