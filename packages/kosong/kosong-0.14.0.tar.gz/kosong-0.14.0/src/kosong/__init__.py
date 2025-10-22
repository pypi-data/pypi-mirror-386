import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from kosong.base import generate
from kosong.base.chat_provider import ChatProvider, StreamedMessagePart, TokenUsage
from kosong.base.message import Message, ToolCall
from kosong.chat_provider import ChatProviderError
from kosong.tooling import ToolResult, ToolResultFuture, Toolset
from kosong.utils.aio import Callback


async def step(
    chat_provider: ChatProvider,
    system_prompt: str,
    toolset: Toolset,
    history: Sequence[Message],
    *,
    on_message_part: Callback[[StreamedMessagePart], None] | None = None,
    on_tool_result: Callable[[ToolResult], None] | None = None,
) -> "StepResult":
    """
    Run one "step". In one step, the function generates LLM response based on the given context for
    exactly one time. All new message parts will be streamed to `on_message_part` in real-time if
    provided. Tool calls will be handled by `context.toolset`. The combined message will be returned
    in a `StepResult`. Depending on the toolset implementation, the tool calls may be handled
    asynchronously and the results need to be fetched by `await step_result.tool_results()`.

    The context will NOT be modified in this function.

    The token usage will be returned in the `StepResult` if available.

    Raises:
        ChatProviderError: If the chat provider fails to generate the message.
        asyncio.CancelledError: If the step is cancelled.
    """

    tool_calls: list[ToolCall] = []
    tool_result_futures: dict[str, ToolResultFuture] = {}

    def future_done_callback(future: ToolResultFuture):
        if on_tool_result:
            try:
                result = future.result()
                on_tool_result(result)
            except asyncio.CancelledError:
                return

    async def on_tool_call(tool_call: ToolCall):
        tool_calls.append(tool_call)
        result = toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            future = ToolResultFuture()
            future.add_done_callback(future_done_callback)
            future.set_result(result)
            tool_result_futures[tool_call.id] = future
        else:
            result.add_done_callback(future_done_callback)
            tool_result_futures[tool_call.id] = result

    try:
        message, usage = await generate(
            chat_provider,
            system_prompt,
            toolset.tools,
            history,
            on_message_part=on_message_part,
            on_tool_call=on_tool_call,
        )
    except (ChatProviderError, asyncio.CancelledError):
        # cancel all the futures to avoid hanging tasks
        for future in tool_result_futures.values():
            future.remove_done_callback(future_done_callback)
            future.cancel()
        raise

    return StepResult(message, usage, tool_calls, tool_result_futures)


@dataclass(frozen=True)
class StepResult:
    message: Message
    """The combined message generated in this step."""

    usage: TokenUsage | None
    """The token usage of the generated message."""

    tool_calls: list[ToolCall]
    """All the tool calls generated in this step."""

    _tool_result_futures: dict[str, ToolResultFuture]
    """The futures of the results of the spawned tool calls."""

    async def tool_results(self) -> list[ToolResult]:
        """All the tool results returned by corresponding tool calls."""
        if not self._tool_result_futures:
            return []

        try:
            results: list[ToolResult] = []
            for tool_call in self.tool_calls:
                result = await self._tool_result_futures[tool_call.id]
                results.append(result)
            return results
        finally:
            # one exception should cancel all the futures to avoid hanging tasks
            for future in self._tool_result_futures.values():
                future.cancel()
