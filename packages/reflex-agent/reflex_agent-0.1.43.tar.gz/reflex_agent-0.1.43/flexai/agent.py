"""Core agent definitions and functionality for the FlexAI framework.

Defines the Agent class for managing conversations, invoking tools, and
interacting with language models. Provides core functionality for creating
flexible AI agents capable of using various tools and capabilities to assist users.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import AsyncGenerator, Callable, Sequence
from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Unpack

from flexai.capability import Capability
from flexai.llm import Client, DefaultClient
from flexai.llm.client import PartialAgentRunArgs
from flexai.message import (
    AIMessage,
    Message,
    MessageContent,
    SystemMessage,
    TextBlock,
    ThoughtBlock,
    ToolCall,
    ToolResult,
    ToolUseChunk,
    UserMessage,
)
from flexai.tool import Tool, send_message


@dataclass(kw_only=True)
class AgentEnv:
    """The Agent's environment. Passed around to components that want access to the outside world."""


@dataclass(frozen=True, kw_only=True)
class Agent:
    """LLM-powered agent using tools and capabilities to interact with users.

    Manages conversation flow, invokes tools, and leverages a language model
    to generate responses. Supports customization through capabilities and
    a flexible toolset.
    """

    # The system prompt to use for the agent.
    prompt: str | SystemMessage = ""

    # A list of functions that the agent can call and use
    tools: list[Callable] = field(default_factory=list, repr=False)

    # A list of tools that, when called, will terminate the conversation.
    terminating_tools: list[Callable] = field(
        default_factory=lambda: [send_message], repr=False
    )

    # Hooks that can plugin to the main agent loop to modify its behavior.
    capabilities: list[Capability] = field(default_factory=list)

    # The language model to use for the agent.
    llms: Sequence[Client] = field(default_factory=lambda: [DefaultClient()])

    # The context that the agent is working in.
    agent_env: AgentEnv = field(default_factory=AgentEnv)

    # The mapping of tool names to tool functions.
    toolbox: dict[str, Tool] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Perform post-initialization setup.

        Raises:
            ValueError: If no clients were provided.
        """
        tools = self.tools or []

        if not self.llms:
            raise ValueError(
                "Agent must be instantiated with at least one LLM client.",
            )

        # Convert callables to tools and store them in the toolbox.
        tools = {Tool.from_function(tool) for tool in set(tools)}
        tools = {tool.name: tool for tool in tools}

        # Hack around dataclass immutability.
        object.__setattr__(self, "toolbox", tools)

        # Setup the capabilities.
        for capability in self.capabilities:
            capability.setup(self)

    async def modify_messages(
        self, messages: list[Message]
    ) -> AsyncGenerator[MessageContent | Message | list[Message], None]:
        """Hook to modify the messages before sending them to the LLM.

        Args:
            messages: The current conversation messages.

        Yields:
            Intermediate message chunks followed by the modified list of messages.

        Raises:
            ValueError: If modified messages were not yielded from a capability.
        """
        # Iterate through the capabilities and modify the messages.
        for capability in self.capabilities:
            modified_messages = None
            async for output in capability.modify_messages(copy(messages)):
                # This is a partial message chunk.
                if isinstance(output, (MessageContent, Message)):
                    yield output

                # This is the modified list of messages.
                else:
                    modified_messages = output

            if modified_messages is None:
                raise ValueError(
                    f"Modified messages were not yielded from {capability}"
                )
            messages = modified_messages

        yield messages

    async def get_system_message(
        self,
    ) -> AsyncGenerator[MessageContent | SystemMessage, None]:
        """Hook to modify the system message before sending it to the LLM.

        Yields:
            Intermediate message chunks followed by the modified system message.
        """
        system = deepcopy(self.prompt)
        if isinstance(system, str):
            system = SystemMessage(system)

        # Iterate through the capabilities and modify the system message.
        for capability in self.capabilities:
            async for output in capability.modify_prompt(system):
                # This is a partial message chunk.
                if isinstance(output, MessageContent):
                    yield output

                # This is the modified system message.
                elif isinstance(output, SystemMessage):
                    system = output

        # Return the system message.
        yield system

    async def get_tools(
        self,
    ) -> AsyncGenerator[MessageContent | Sequence[Tool], None]:
        """Hook to modify the tool list before sending it to the LLM.

        Yields:
            Intermediate message chunks followed by the modified tool list.
        """
        tools = list(self.toolbox.values())

        for capability in self.capabilities:
            async for output in capability.modify_tools(tools):
                # This is a partial message chunk.
                if isinstance(output, MessageContent):
                    yield output

                # This is the modified tool list.
                else:
                    tools = output

        # Return the tools.
        yield tools

    async def modify_response(
        self, messages: list[Message], response: AIMessage
    ) -> AsyncGenerator[MessageContent | AIMessage, None]:
        """Hook to modify the AI response before sending it to the user.

        Args:
            messages: The current conversation messages.
            response: The AI response.

        Yields:
            Intermediate message chunks followed by the modified AI response.

        Raises:
            ValueError: If modified response was not yielded from capability.
        """
        # Iterate through the capabilities and modify the response.
        for capability in self.capabilities:
            # Our final response
            modified_response = None

            async for output in capability.modify_response(messages, response):
                # This is a partial message chunk.
                if isinstance(output, MessageContent):
                    yield output

                # This is the modified AI response.
                else:
                    # This is a full piece of content (presumably a message) that we want to take note of
                    if modified_response:
                        yield modified_response
                    modified_response = output

            if modified_response is None:
                raise ValueError(f"Modified response was not yielded from {capability}")

            response = modified_response

        yield response

    async def invoke_tool(
        self, tool_call: ToolCall, messages: list[Message]
    ) -> AsyncGenerator[MessageContent | Message, None]:
        """Execute a tool and yield progress before returning the final result.

        Args:
            tool_call: The tool call to execute.
            messages: The current conversation messages.

        Yields:
            Intermediate message chunks followed by the final tool result.

        """
        try:
            tool = self.toolbox[tool_call.name]
        except KeyError:
            yield ToolResult(
                tool_call_id=tool_call.id,
                result=TextBlock(
                    text=f"The tool `{tool_call.name}` is not available to you."
                ),
                execution_time=0,
                is_error=True,
            )
            return

        is_error = False

        # Add the context to the tool input.
        kwargs = tool_call.input.copy()
        if tool.requires_context:
            # Add the current messages.
            kwargs["messages"] = messages

            # Add the agent instance.
            kwargs["agent_env"] = self.agent_env

        start_time = time.monotonic()
        try:
            if asyncio.iscoroutinefunction(tool.fn):
                result = await tool.fn(**kwargs)
            else:
                result = tool.fn(**kwargs)

            if isinstance(result, AsyncGenerator):
                last_received = None
                async with contextlib.aclosing(result) as result:
                    async for intermediate in result:
                        if last_received is not None:
                            yield ToolUseChunk(
                                id=tool_call.id,
                                tool_name=tool_call.name,
                                content=last_received,
                            )
                            last_received = None
                        if isinstance(intermediate, (Message, ToolResult)):
                            yield intermediate
                            continue
                        last_received = intermediate
                    result = last_received

        except Exception as e:
            result = f"({tool_call.name}) {e!s}"
            is_error = True

        end_time = time.monotonic()

        yield ToolResult(
            tool_call_id=tool_call.id,
            result=result,
            execution_time=end_time - start_time,
            is_error=is_error,
        )

    async def modify_tool_results(
        self,
        messages: list[Message],
        tool_call_message: Message[Sequence[MessageContent] | str],
        tool_results: list[MessageContent],
    ) -> AsyncGenerator[Message | MessageContent, None]:
        """Hook to modify the tool calls and results before sending them to the user.

        All of the input arguments (messages, tool_call_message, and tool_results) may be modified in
        place.

        If followup messages are yielded, this will override terminating tool
        determination.

        Args:
            messages: The current conversation messages.
            tool_call_message: The AI message containing the tool call(s).
            tool_results: The ToolResult fragments, should correspond 1:1
                with calls in tool_call_message.

        Yields:
            Intermediate message chunks or followup messages to continue the loop.
        """
        # Iterate through the capabilities and modify the tool results.
        for capability in self.capabilities:
            async for output in capability.modify_tool_results(
                messages=copy(messages),
                tool_call_message=tool_call_message,
                tool_results=tool_results,
            ):
                yield output

    async def _get_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        tools: Sequence[Tool],
        current_llm_index: int = 0,
        llm_exception_callback: Callable[[Exception, int], bool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ):
        """Get a chat response from the LLM with automatic fallback between clients.

        Attempts to get a response from the current LLM client. If an exception
        occurs, optionally uses the callback to determine whether to retry with
        the next client in the list.

        Args:
            messages: The conversation messages to send to the LLM.
            system: The system message or prompt.
            tools: The available tools for the LLM to use.
            current_llm_index: Index of the current LLM client to use.
            llm_exception_callback: Optional callback to determine retry behavior
                when exceptions occur. Receives the exception and current LLM index,
                returns True to retry with next client, False to raise the exception.
            **input_args: Additional arguments to pass to the LLM client.

        Returns:
            The AI response message from the LLM.

        Raises:
            Exception: Any exception from the LLM client if no more retries available
                or callback indicates not to retry.
        """
        try:
            return await self.llms[current_llm_index].get_chat_response(
                messages,
                system=system,
                tools=tools,
                **input_args,
            )

        except Exception as e:
            # Whether we should retry on this exception
            should_retry = True

            # If the caller provided a callback, obtain a recommendation for whether to retry
            if llm_exception_callback is not None:
                should_retry = llm_exception_callback(e, current_llm_index)

            # If we have no more clients to try, raise
            if current_llm_index == len(self.llms) - 1:
                should_retry = False

            if not should_retry:
                raise

            return await self._get_chat_response(
                messages=messages,
                system=system,
                tools=tools,
                current_llm_index=current_llm_index + 1,
                llm_exception_callback=llm_exception_callback,
                **input_args,
            )

    async def _stream_chat_response(
        self,
        messages: list[Message],
        system: str | SystemMessage,
        tools: Sequence[Tool],
        current_llm_index: int = 0,
        llm_exception_callback: Callable[[Exception, int], bool] | None = None,
        **input_args: Unpack[PartialAgentRunArgs],
    ):
        """Stream a chat response from the LLM with automatic fallback between clients.

        Attempts to stream a response from the current LLM client. If an exception
        occurs, optionally uses the callback to determine whether to retry with
        the next client in the list.

        Args:
            messages: The conversation messages to send to the LLM.
            system: The system message or prompt.
            tools: The available tools for the LLM to use.
            current_llm_index: Index of the current LLM client to use.
            llm_exception_callback: Optional callback to determine retry behavior
                when exceptions occur. Receives the exception and current LLM index,
                returns True to retry with next client, False to raise the exception.
            **input_args: Additional arguments to pass to the LLM client.

        Yields:
            Streaming chunks of the AI response from the LLM.

        Raises:
            Exception: Any exception from the LLM client if no more retries available
                or callback indicates not to retry.
        """
        try:
            # Try streaming on this client.
            async for output in self.llms[current_llm_index].stream_chat_response(
                messages=messages,
                system=system,
                tools=tools,
                **input_args,
            ):
                yield output

        except Exception as e:
            # Whether we should retry on this exception
            should_retry = True

            # If the caller provided a callback, obtain a recommendation for whether to retry
            if llm_exception_callback is not None:
                should_retry = llm_exception_callback(e, current_llm_index)

            # If we have no more clients to try, raise
            if current_llm_index == len(self.llms) - 1:
                should_retry = False

            if not should_retry:
                raise

            # Try the next LLM in our list of options
            async for output in self._stream_chat_response(
                messages=messages,
                system=system,
                tools=tools,
                current_llm_index=current_llm_index + 1,
                llm_exception_callback=llm_exception_callback,
                **input_args,
            ):
                yield output

    async def step(
        self,
        messages: list[Message],
        stream: bool,
        llm_exception_callback: Callable[[Exception, int], bool] | None = None,
        **run_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncGenerator[MessageContent | Message | list[Message], None]:
        """Process a single turn in the conversation.

        Generates a response using the language model and determines if any
        tools need to be invoked based on the current conversation state.

        Args:
            messages: Current conversation messages.
            stream: Whether to stream the response.
            llm_exception_callback: Optional callback to determine retry behavior
                when LLM exceptions occur. Receives the exception and current LLM index,
                returns True to retry with next client, False to raise the exception.
            **run_args: Additional arguments including allow_tool, force_tool,
                thinking_budget, model, temperature, raise_on_null_content and other
                keyword arguments to pass to the client.

        Yields:
            Partial chunks of the tool response, if streaming is on.

        Returns:
            The generated responses, including potential tool use messages.

        Raises:
            ValueError: If no response received from LLM or modified response was not yielded.
        """
        # Preprocess the messages and get the system message.
        async for output in self.modify_messages(messages):
            # This is a partial message chunk.
            if isinstance(output, (MessageContent, Message)):
                yield output

            # This is the modified list of messages.
            else:
                messages = output

        # The runner will want the capability-modified messages
        yield messages

        system = ""
        async for output in self.get_system_message():
            # This is a partial message chunk.
            if isinstance(output, MessageContent):
                yield output

            # This is the modified system message.
            else:
                system = output

        tools = []
        async for output in self.get_tools():
            # This is a partial message chunk
            if isinstance(output, MessageContent):
                yield output

            # This is the modified tool list.
            else:
                tools = output

        if stream:
            response = None
            async for chunk in self._stream_chat_response(
                messages,
                system=system,
                tools=tools,
                llm_exception_callback=llm_exception_callback,
                **run_args,
            ):
                # This is a partial message chunk.
                if isinstance(chunk, MessageContent):
                    yield chunk

                # This is the final message.
                else:
                    response = chunk
        else:
            # Get the response from the LLM.
            response = await self._get_chat_response(
                messages,
                system=system,
                tools=tools,
                llm_exception_callback=llm_exception_callback,
                **run_args,
            )

        if response is None:
            raise ValueError(f"No response received from the LLM {self.llms}.")

        modified_response = None

        # Modify the response.
        async for output in self.modify_response(messages, response):
            # This is a partial message chunk.
            if isinstance(output, MessageContent):
                yield output

            # This is the modified AI response.
            else:
                # This is a full piece of content (presumably a message) that we want to take note of
                if modified_response:
                    yield modified_response
                modified_response = output

        if modified_response is None:
            raise ValueError("Modified response was not yielded")

        response = modified_response

        # Base case: send_message tool call.
        if (
            (
                isinstance(response.content, Sequence)
                and not isinstance(response.content, str)
            )
            and len(response.content) > 0
            and isinstance(response.content[0], ToolCall)
            and any(
                response.content[0].name == tool.__name__
                for tool in self.terminating_tools
            )
        ):
            if response.content[0].name == "send_message":
                response.content = response.content[0].input["message"]
            yield response
            return

        # Return the response.
        yield response

    async def run(
        self,
        messages: list[Message],
        stream: bool = False,
        llm_exception_callback: Callable[[Exception, int], bool] | None = None,
        **run_args: Unpack[PartialAgentRunArgs],
    ) -> AsyncGenerator[MessageContent | Message, None]:
        """Generate an asynchronous stream of agent responses and tool invocations.

        Processes conversation steps and invokes tools until a final response
        (non-tool use message) is generated.

        Args:
            messages: Initial conversation messages.
            stream: Whether to stream the response.
            llm_exception_callback: Optional callback to determine retry behavior
                when LLM exceptions occur. Receives the exception and current LLM index,
                returns True to retry with next client, False to raise the exception.
            **run_args: Additional arguments including allow_tool, force_tool,
                thinking_budget, model, temperature, raise_on_null_content and other
                keyword arguments to pass to the client.

        Yields:
            Message: Each message in the conversation, including tool uses and results.

        Returns:
            If we receive a non-tool use message, the function will terminate.

        Raises:
            ValueError: If no response received from LLM, modified messages not available, or tool call did not yield result.
        """
        # Run in a loop.
        while True:
            # Get the response and yield
            response = None

            # Obtain the modified messages as well (because some tools might actually want them)
            modified_messages = None

            async for output in self.step(
                messages,
                stream,
                llm_exception_callback=llm_exception_callback,
                **run_args,
            ):
                # This is a partial message chunk.
                if isinstance(output, MessageContent):
                    yield output

                # This is the modified list of messages.
                if (
                    isinstance(output, Sequence) and not isinstance(output, str)
                ) and all(isinstance(message, Message) for message in output):
                    modified_messages = output

                # This *could be* the final message.
                if isinstance(output, Message):
                    yield copy(output)
                    response = output

            if response is None:
                raise ValueError(f"No response received from the LLM {self.llms}.")

            if modified_messages is None:
                raise ValueError("Modified messages are not available")

            messages = modified_messages

            # If it's not a tool use, end the stream.
            if not isinstance(response.content, Sequence) or not any(
                isinstance(message, ToolCall) for message in response.content
            ):
                return

            results = []
            last_tool_call = None
            for tool_call in response.content:
                if isinstance(tool_call, ToolCall):
                    result = None
                    last_tool_call = tool_call
                    async for intermediate in self.invoke_tool(tool_call, messages):
                        if isinstance(
                            intermediate, (ThoughtBlock, MessageContent, Message)
                        ):
                            yield intermediate
                        result = intermediate
                    if result is None:
                        raise ValueError(
                            f"Tool call {tool_call} did not yield a result."
                        )
                    results.append(result)
            # Hook to modify tool results or perform post-tool processing.
            async for output in self.modify_tool_results(
                messages=messages,
                tool_call_message=response,
                tool_results=results,
            ):
                yield output

            # Add the tool results message to the thread.
            messages.append(response)
            result_message = UserMessage(results)
            messages.append(result_message)
            yield result_message

            if isinstance(last_tool_call, ToolCall) and any(
                last_tool_call.name == tool.__name__ for tool in self.terminating_tools
            ):
                break
