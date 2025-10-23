"""
Base agent implementation following the stub.md specification.

This module provides the core BaseAgent class that all agents must inherit from,
implementing the interface specified in stub.md with proper typing and functionality.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel

from .._cancellation_token import CancellationToken
from .._component_config import ComponentBase
from .._middleware import BaseMiddleware, MiddlewareChain
from ..context import AgentContext
from ..llm import BaseChatCompletionClient
from ..memory import BaseMemory
from ..messages import Message, SystemMessage, UserMessage
from ..tools import BaseTool, FunctionTool
from ..types import AgentEvent, AgentResponse, ChatCompletionChunk, Usage

if TYPE_CHECKING:
    from ._agent_as_tool import AgentAsTool


class BaseAgent(ComponentBase[BaseModel], ABC):
    """
    Abstract base class defining the core agent interface.

    All agents in the picoagents framework must inherit from this base class
    and implement its abstract methods, following the stub.md specification.
    """

    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        model_client: BaseChatCompletionClient,
        tools: Optional[List[Union[BaseTool, Callable]]] = None,
        memory: Optional[BaseMemory] = None,
        context: Optional[AgentContext] = None,
        middlewares: Optional[List[BaseMiddleware]] = None,
        max_iterations: int = 10,
        output_format: Optional[Type[BaseModel]] = None,
        summarize_tool_result: bool = True,
        required_tools: Optional[List[str]] = None,
        example_tasks: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """
        Initialize the base agent following stub.md specification.

        Args:
            name: Unique identifier for the agent
            description: External-facing description for orchestrators/other agents
            instructions: Internal system prompt/role definition for LLM calls
            model_client: Abstraction for LLM API calls
            tools: Available tools for the agent
            memory: Persistent storage for agent state
            context: Agent context containing messages and metadata
            middlewares: List of middleware to process operations
            max_iterations: Maximum tool call iterations to prevent loops
            output_format: Optional Pydantic model for structured output
            summarize_tool_result: If False, agent stops after tool execution without LLM summarization
            required_tools: Optional list of tool names that MUST be used (forced tool use)
            example_tasks: Optional list of example tasks to help users discover agent capabilities
            **kwargs: Additional configuration
        """
        self.name = name
        self.description = description
        self.instructions = instructions
        self.model_client = model_client
        self.tools = self._process_tools(tools or [])
        self.memory = memory
        self.context = context or AgentContext()
        self.middleware_chain = MiddlewareChain(middlewares)
        self.max_iterations = max_iterations
        self.output_format = output_format
        self.summarize_tool_result = summarize_tool_result
        self.required_tools = required_tools or []
        self.example_tasks = example_tasks or []

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate agent configuration."""
        if not self.name or not isinstance(self.name, str):
            raise AgentConfigurationError("Agent name must be a non-empty string")

        if not self.description:
            raise AgentConfigurationError("Agent description cannot be empty")

        if not self.instructions:
            raise AgentConfigurationError("Agent instructions cannot be empty")

        if self.model_client is None:
            raise AgentConfigurationError("Model client is required")

    def _process_tools(self, tools: List[Union[BaseTool, Callable]]) -> List[BaseTool]:
        """
        Convert mixed tool types to BaseTool instances.

        Args:
            tools: List of BaseTool instances or callable functions

        Returns:
            List of BaseTool instances
        """
        processed = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                processed.append(tool)
            elif callable(tool):
                processed.append(FunctionTool(tool))
            else:
                raise AgentConfigurationError(
                    f"Invalid tool type: {type(tool)}. Must be BaseTool or callable."
                )
        return processed

    def _find_tool(self, name: str) -> Optional[BaseTool]:
        """
        Find tool by name.

        Args:
            name: Tool name to search for

        Returns:
            Tool instance or None if not found
        """
        return next((tool for tool in self.tools if tool.name == name), None)

    def _get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Convert tools to OpenAI function calling format.

        Returns:
            List of tools in OpenAI function format
        """
        return [tool.to_llm_format() for tool in self.tools]

    @abstractmethod
    async def run(
        self,
        task: Union[str, UserMessage, List[Message]],
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AgentResponse:
        """
        Execute the agent's main reasoning and action loop.

        Args:
            task: The task or query for the agent to address
            cancellation_token: Optional token for cancelling execution

        Returns:
            AgentResponse containing messages and usage statistics

        Raises:
            AgentError: If the agent encounters an error during execution
            asyncio.CancelledError: If execution is cancelled
        """
        pass

    @abstractmethod
    def run_stream(
        self,
        task: Union[str, UserMessage, List[Message]],
        cancellation_token: Optional[CancellationToken] = None,
        verbose: bool = False,
        stream_tokens: bool = False,
    ) -> AsyncGenerator[
        Union[Message, AgentEvent, AgentResponse, ChatCompletionChunk], None
    ]:
        """
        Execute the agent with streaming output.

        Args:
            task: The task or query for the agent to address
            cancellation_token: Optional token for cancelling execution
            verbose: If True, emit agent events; if False, only emit messages and response
            stream_tokens: If True, stream individual token chunks from LLM (implementation dependent)

        Yields:
            Messages, events (if verbose=True), ChatCompletionChunks (if stream_tokens=True), and final AgentResponse with usage stats

        Raises:
            AgentError: If the agent encounters an error during execution
            asyncio.CancelledError: If execution is cancelled
        """
        pass

    def _convert_task_to_messages(
        self, task: Union[str, UserMessage, List[Message]]
    ) -> List[Message]:
        """
        Convert task input to proper message format.

        Args:
            task: Task in various formats

        Returns:
            List of messages
        """
        if isinstance(task, str):
            return [UserMessage(content=task, source="user")]
        elif isinstance(task, UserMessage):
            return [task]
        elif isinstance(task, list):
            return task
        else:
            raise AgentExecutionError(f"Unsupported task type: {type(task)}")

    async def _prepare_llm_messages(
        self, task_messages: List[Message]
    ) -> List[Message]:
        """
        Prepare messages for LLM call including system instructions, memory context, and history.

        Args:
            task_messages: Messages from the current task

        Returns:
            Complete list of messages for LLM
        """
        messages = []

        # Add system message with instructions
        system_content = self.instructions

        # Add forced tool use instruction if required_tools is set
        if self.required_tools:
            tool_list = ", ".join(self.required_tools)
            system_content += f"\n\nIMPORTANT: You MUST use these tools in your response: {tool_list}. Do not respond without calling these tools."

        # Add memory context if available
        if self.memory:
            try:
                # Get relevant context from memory based on current task
                current_task = task_messages[0].content if task_messages else ""
                memory_result = await self.memory.get_context(max_items=5)

                # Handle both old (List[str]) and new (MemoryQueryResult) interfaces
                if hasattr(memory_result, "results"):
                    # New MemoryQueryResult interface
                    context_items = []
                    for memory_content in memory_result.results:
                        if isinstance(memory_content.content, str):
                            context_items.append(memory_content.content)
                        else:
                            # Handle dict/json content
                            import json

                            context_items.append(json.dumps(memory_content.content))
                    context = context_items
                else:
                    # Legacy List[str] interface (backward compatibility)
                    context = memory_result

                if context and isinstance(context, list):
                    system_content += "\n\nRelevant context from memory:\n" + "\n".join(
                        context
                    )
            except Exception:
                # Don't fail if memory access fails
                pass

        messages.append(SystemMessage(content=system_content, source="system"))

        # Add message history from context
        messages.extend(self.context.messages)

        # Add current task messages
        messages.extend(task_messages)

        return messages

    async def reset(self) -> None:
        """
        Reset the agent to a clean state.

        Clears conversation history and temporary state while preserving
        core configuration.
        """
        self.context.reset()

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the agent for debugging and coordination.

        Returns:
            Dictionary containing agent metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "model": getattr(self.model_client, "model", "unknown"),
            "tools_count": len(self.tools),
            "has_memory": self.memory is not None,
            "has_middlewares": len(self.middleware_chain.middlewares) > 0,
            "message_history_length": self.context.message_count,
        }

    def get_conversation_data(self) -> Dict[str, Any]:
        """
        Get current conversation data for application-managed memory storage.

        Returns:
            Dictionary containing conversation context that applications can use
            to decide what to store in memory
        """
        from ..messages import AssistantMessage, ToolMessage, UserMessage

        user_messages = [
            msg for msg in self.context.messages if isinstance(msg, UserMessage)
        ]
        assistant_messages = [
            msg for msg in self.context.messages if isinstance(msg, AssistantMessage)
        ]
        tool_messages = [
            msg for msg in self.context.messages if isinstance(msg, ToolMessage)
        ]

        return {
            "agent_name": self.name,
            "total_messages": self.context.message_count,
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "tool_messages": len(tool_messages),
            "tools_used": list(
                set([msg.tool_name for msg in tool_messages if msg.success])
            ),
            "last_user_message": user_messages[-1].content if user_messages else None,
            "last_assistant_message": assistant_messages[-1].content
            if assistant_messages
            else None,
            "session_id": self.context.session_id,
            "metadata": self.context.metadata,
            "conversation_history": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content[:200] + "..."
                    if len(msg.content) > 200
                    else msg.content,
                    "timestamp": getattr(msg, "timestamp", None),
                }
                for msg in self.context.messages
            ],
        }

    def as_tool(self, task_parameter_name: str = "task") -> "AgentAsTool":
        """
        Convert this agent into a tool that other agents can use.

        This enables hierarchical composition where specialized agents can be
        used as tools by higher-level coordinating agents.

        Args:
            task_parameter_name: Parameter name for the task input (default: "task")

        Returns:
            AgentAsTool instance wrapping this agent
        """
        from ._agent_as_tool import AgentAsTool

        return AgentAsTool(self, task_parameter_name)

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description[:50]}...')"

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager with cleanup."""
        # Subclasses can override to add specific cleanup
        # Default behavior: no cleanup needed for base agent
        return False


class AgentError(Exception):
    """Base exception class for agent-related errors."""

    def __init__(self, message: str, agent_name: Optional[str] = None):
        self.agent_name = agent_name
        super().__init__(message)

    def __str__(self) -> str:
        if self.agent_name:
            return f"Agent '{self.agent_name}': {super().__str__()}"
        return super().__str__()


class AgentExecutionError(AgentError):
    """Raised when an agent encounters an error during task execution."""

    pass


class AgentConfigurationError(AgentError):
    """Raised when an agent is misconfigured."""

    pass


class AgentToolError(AgentError):
    """Raised when an agent's tool execution fails."""

    pass


class AgentMemoryError(AgentError):
    """Raised when agent memory operations fail."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    pass
