"""
Tool execution event dataclasses.

Events for tool execution lifecycle, mirroring agent.hooks.tool.* structure:
- Start: Tool execution started
- Done: Tool execution completed
- Error: Tool execution failed
- CallPre: Before individual tool call
- CallPost: After individual tool call
- TaskStarted: Async tool task started
- TaskCompleted: Async tool task completed
- TaskFailed: Async tool task failed
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Start:
    """
    Tool execution started event.

    Emitted from HookType.BEFORE_TOOL_EXECUTION.
    Corresponds to @agent.hooks.tool.pre_exec decorator.
    """
    tool_name: str
    params: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Done:
    """
    Tool execution completed event.

    Emitted from HookType.AFTER_TOOL_EXECUTION.
    Corresponds to @agent.hooks.tool.post_exec decorator.
    """
    tool_name: str
    result: Any
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Error:
    """
    Tool execution failed event.

    Emitted from HookType.ON_TOOL_ERROR.
    Corresponds to @agent.hooks.tool.on_error decorator.
    """
    tool_name: str
    error: Exception
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallPre:
    """
    Before individual tool call event.

    Emitted from HookType.BEFORE_TOOL_CALL.
    Corresponds to @agent.hooks.tool.pre_call decorator.
    """
    tool_name: str
    params: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallPost:
    """
    After individual tool call event.

    Emitted from HookType.AFTER_TOOL_CALL.
    Corresponds to @agent.hooks.tool.post_call decorator.
    """
    tool_name: str
    result: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStarted:
    """
    Async tool task started event.

    Emitted from HookType.ON_TOOL_TASK_STARTED.
    Corresponds to @agent.hooks.tool.on_async_start decorator.
    """
    task_id: str
    tool_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskCompleted:
    """
    Async tool task completed event.

    Emitted from HookType.ON_TOOL_TASK_COMPLETED.
    Corresponds to @agent.hooks.tool.on_async_complete decorator.
    """
    task_id: str
    tool_name: str
    result: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskFailed:
    """
    Async tool task failed event.

    Emitted from HookType.ON_TOOL_TASK_FAILED.
    Corresponds to @agent.hooks.tool.on_async_failed decorator.
    """
    task_id: str
    tool_name: str
    error: Exception
    metadata: Dict[str, Any] = field(default_factory=dict)
