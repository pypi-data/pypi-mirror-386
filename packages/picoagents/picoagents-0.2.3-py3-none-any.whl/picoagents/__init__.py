"""
Picoagents Framework

A lightweight, type-safe framework for building AI agents with LLMs.
Supports tool calling, memory, streaming, and multi-agent orchestration.
"""

# Auto-instrument with OpenTelemetry if enabled
import os

if os.getenv("PICOAGENTS_ENABLE_OTEL", "false").lower() in ("true", "1", "yes"):
    try:
        from ._otel import auto_instrument

        auto_instrument()
    except Exception:
        pass  # Gracefully continue if instrumentation fails

# Cancellation support
from ._cancellation_token import CancellationToken

# Component configuration system
from ._component_config import (
    Component,
    ComponentBase,
    ComponentFromConfig,
    ComponentLoader,
    ComponentModel,
    ComponentSchemaType,
    ComponentToConfig,
    ComponentType,
)

# Middleware system
from ._middleware import (
    BaseMiddleware,
    GuardrailMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    MiddlewareChain,
    MiddlewareContext,
    PIIRedactionMiddleware,
    RateLimitMiddleware,
)

# Agent implementations
from .agents import (
    Agent,
    AgentConfigurationError,
    AgentError,
    AgentExecutionError,
    AgentToolError,
    BaseAgent,
)

# Evaluation system
from .eval import (
    AgentEvalTarget,
    BaseEvalRunner,
    BaseEvalTarget,
    EvalRunner,
    LLMEvalJudge,
    ModelEvalTarget,
    OrchestratorEvalTarget,
)

# LLM clients
from .llm import (
    AuthenticationError,
    BaseChatCompletionClient,
    BaseChatCompletionError,
    InvalidRequestError,
    OpenAIChatCompletionClient,
    RateLimitError,
)

# Memory system
from .memory import BaseMemory, FileMemory, ListMemory, MemoryContent, MemoryQueryResult

# Context system
from .context import (
    AgentContext,
    ToolApprovalRequest,
    ToolApprovalResponse,
)

# Core message types
from .messages import (
    AssistantMessage,
    Message,
    MultiModalMessage,
    SystemMessage,
    ToolCallRequest,
    ToolMessage,
    UserMessage,
)

# Orchestration patterns
from .orchestration import (
    BaseOrchestrator,
    BaseTermination,
    CancellationTermination,
    CompositeTermination,
    ExternalTermination,
    FunctionCallTermination,
    HandoffTermination,
    MaxMessageTermination,
    RoundRobinOrchestrator,
    TextMentionTermination,
    TimeoutTermination,
    TokenUsageTermination,
)

# Tool system
from .tools import ApprovalMode, BaseTool, FunctionTool, tool

# Core data types
from .types import (
    AgentEvent,
    AgentResponse,
    ChatCompletionChunk,
    ChatCompletionResult,
    OrchestrationEvent,
    OrchestrationResponse,
    StopMessage,
    ToolResult,
    Usage,
)

# Workflow system
from .workflow import (
    BaseStep,
    Context,
    EchoStep,
    FunctionStep,
    HttpStep,
    PicoAgentStep,
    StepMetadata,
    TransformStep,
    Workflow,
    WorkflowMetadata,
    WorkflowRunner,
)

__version__ = "0.1.2"

__all__ = [
    # Context
    "AgentContext",
    "ToolApprovalRequest",
    "ToolApprovalResponse",
    # Messages
    "Message",
    "SystemMessage",
    "UserMessage",
    "AssistantMessage",
    "ToolMessage",
    "MultiModalMessage",
    "ToolCallRequest",
    # Types
    "Usage",
    "ToolResult",
    "AgentResponse",
    "ChatCompletionResult",
    "ChatCompletionChunk",
    "AgentEvent",
    "StopMessage",
    "OrchestrationResponse",
    "OrchestrationEvent",
    # Cancellation
    "CancellationToken",
    # Component Configuration
    "ComponentModel",
    "ComponentFromConfig",
    "ComponentToConfig",
    "ComponentSchemaType",
    "ComponentLoader",
    "ComponentBase",
    "Component",
    "ComponentType",
    # Agents
    "BaseAgent",
    "Agent",
    "AgentError",
    "AgentExecutionError",
    "AgentConfigurationError",
    "AgentToolError",
    # Tools
    "BaseTool",
    "FunctionTool",
    "ApprovalMode",
    "tool",
    # Memory
    "BaseMemory",
    "MemoryContent",
    "MemoryQueryResult",
    "ListMemory",
    "FileMemory",
    # LLM
    "BaseChatCompletionClient",
    "BaseChatCompletionError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
    "OpenAIChatCompletionClient",
    # Orchestration
    "BaseOrchestrator",
    "RoundRobinOrchestrator",
    "BaseTermination",
    "MaxMessageTermination",
    "TextMentionTermination",
    "TokenUsageTermination",
    "TimeoutTermination",
    "HandoffTermination",
    "ExternalTermination",
    "CancellationTermination",
    "FunctionCallTermination",
    "CompositeTermination",
    # Workflow system
    "Workflow",
    "WorkflowRunner",
    "BaseStep",
    "FunctionStep",
    "EchoStep",
    "HttpStep",
    "TransformStep",
    "PicoAgentStep",
    "WorkflowMetadata",
    "StepMetadata",
    "Context",
    # Evaluation
    "BaseEvalTarget",
    "BaseEvalRunner",
    "EvalRunner",
    "AgentEvalTarget",
    "ModelEvalTarget",
    "OrchestratorEvalTarget",
    "LLMEvalJudge",
    # Middleware
    "BaseMiddleware",
    "MiddlewareContext",
    "MiddlewareChain",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "PIIRedactionMiddleware",
    "GuardrailMiddleware",
    "MetricsMiddleware",
]
