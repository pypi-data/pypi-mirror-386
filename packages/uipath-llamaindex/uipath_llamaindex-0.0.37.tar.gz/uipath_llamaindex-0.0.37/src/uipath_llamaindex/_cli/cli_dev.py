import asyncio
from typing import Optional

from openinference.instrumentation.llama_index import (
    LlamaIndexInstrumentor,
    get_current_span,
)
from uipath._cli._dev._terminal import UiPathDevTerminal
from uipath._cli._runtime._contracts import UiPathRuntimeFactory
from uipath._cli._utils._console import ConsoleLogger
from uipath._cli.middlewares import MiddlewareResult

from ._runtime._context import UiPathLlamaIndexRuntimeContext
from ._runtime._runtime import UiPathLlamaIndexRuntime

console = ConsoleLogger()


def llamaindex_dev_middleware(interface: Optional[str]) -> MiddlewareResult:
    """Middleware to launch the developer terminal"""

    try:
        if interface == "terminal":
            runtime_factory = UiPathRuntimeFactory(
                UiPathLlamaIndexRuntime, UiPathLlamaIndexRuntimeContext
            )
            runtime_factory.add_instrumentor(LlamaIndexInstrumentor, get_current_span)
            app = UiPathDevTerminal(runtime_factory)
            asyncio.run(app.run_async())
        else:
            console.error(f"Unknown interface: {interface}")
    except KeyboardInterrupt:
        console.info("Debug session interrupted by user")
    except Exception as e:
        console.error(f"Error occurred: {e}")
        return MiddlewareResult(
            should_continue=False,
            should_include_stacktrace=True,
        )

    return MiddlewareResult(should_continue=False)
