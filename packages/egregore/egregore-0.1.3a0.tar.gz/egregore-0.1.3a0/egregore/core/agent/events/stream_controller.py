"""
Agent Event Stream Controller.

Provides AgentEventStream - an async iterator that yields hierarchical events
during agent execution by registering temporary hooks and converting hook
contexts to event dataclasses.
"""

import asyncio
import logging
from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

from ..hooks.execution import HookType
from ..hooks.execution_contexts import (
    ToolExecContext,
    StreamExecContext,
    ScaffoldExecContext,
    ContextExecContext
)

if TYPE_CHECKING:
    from ..base import Agent

logger = logging.getLogger(__name__)


class AgentEventStream:
    """
    Async iterator yielding hierarchical event dataclasses from agent execution.

    Registers temporary hooks during agent processing and converts hook contexts
    to typed events that mirror the hook structure.

    Usage:
        stream = agent.events("Hello, world!", verbose=True)
        async for event in stream:
            match event:
                case events.tool.Start(tool_name=name):
                    print(f"Tool: {name}")
                case events.stream.ContentChunk(text=t):
                    print(t, end="")
                case events.agent.Done():
                    break
    """

    def __init__(
        self,
        agent: 'Agent',
        message: str,
        *,
        verbose: bool = False,
        queue_size: int = 1000,
        coalesce_stream: bool = True
    ):
        """
        Initialize event stream.

        Args:
            agent: Agent instance to monitor
            message: User message to process
            verbose: Include tool/scaffold/context events (default: only stream/agent)
            queue_size: Bounded queue size for backpressure
            coalesce_stream: Coalesce adjacent ContentChunk events
        """
        self.agent = agent
        self.message = message
        self.verbose = verbose
        self.coalesce_stream = coalesce_stream
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._hook_cleanup: list = []
        self._finished = False
        self._execution_id: Optional[str] = None
        self._processing_task: Optional[asyncio.Task] = None

    def __aiter__(self):
        """Return self as async iterator."""
        return self

    async def __anext__(self):
        """
        Yield next event from the stream.

        Returns:
            Next event dataclass

        Raises:
            StopAsyncIteration: When stream completes
        """

        # Start processing on first iteration
        if self._processing_task is None:
            self._register_event_hooks()
            self._processing_task = asyncio.create_task(self._process_with_events())

        # Check if finished
        if self._finished and self.event_queue.empty():
            await self._cleanup_hooks()
            raise StopAsyncIteration

        # Get next event from queue
        event = await self.event_queue.get()
        return event

    def _register_event_hooks(self):
        """
        Register temporary hooks that convert to events.

        Hooks are registered early, but execution_id is set later when agent.astream() starts.
        Hooks will check execution_id at runtime to filter cross-talk.
        """
        hooks = self.agent._hooks_instance


        # Always register stream events (core events)
        # Use ON_STREAMING_CHUNK which is what aprocess_stream_chunk() actually triggers
        hooks.register_hook(HookType.ON_STREAMING_CHUNK, self._emit_content_chunk)

        # Verbose mode: register all event types
        if self.verbose:
            # Tool events - use task-based hooks which fire for both sync and async execution
            # These are the primary hooks fired by ToolTaskLoop during streaming
            hooks.register_hook(HookType.ON_TOOL_TASK_STARTED, self._emit_tool_start)
            hooks.register_hook(HookType.ON_TOOL_TASK_COMPLETED, self._emit_tool_done)
            hooks.register_hook(HookType.ON_TOOL_TASK_FAILED, self._emit_tool_error)

            # Also register execution hooks for completeness (non-streaming path)
            hooks.register_hook(HookType.BEFORE_TOOL_EXECUTION, self._emit_tool_start)
            hooks.register_hook(HookType.AFTER_TOOL_EXECUTION, self._emit_tool_done)
            hooks.register_hook(HookType.ON_TOOL_ERROR, self._emit_tool_error)

            # Tool call hooks (individual calls)
            # CRITICAL: AFTER_TOOL_CALL also emits ToolDone since it fires in the actual execution path
            hooks.register_hook(HookType.BEFORE_TOOL_CALL, self._emit_tool_call_pre)
            hooks.register_hook(HookType.AFTER_TOOL_CALL, self._emit_tool_call_post)
            hooks.register_hook(HookType.AFTER_TOOL_CALL, self._emit_tool_done)

            # Streaming tool detection
            hooks.register_hook(HookType.ON_TOOL_CALL_DETECTED, self._emit_tool_detected)

            # Scaffold events
            hooks.register_hook(HookType.ON_SCAFFOLD_OPERATION_COMPLETED, self._emit_scaffold_complete)
            hooks.register_hook(HookType.ON_SCAFFOLD_STATE_CHANGE, self._emit_scaffold_state_change)

            # Context events
            hooks.register_hook(HookType.CONTEXT_AFTER_CHANGE, self._emit_context_updated)

        # Track hooks for cleanup
        self._hook_cleanup.append(HookType.ON_CONTENT_CHUNK)
        if self.verbose:
            self._hook_cleanup.extend([
                HookType.BEFORE_TOOL_EXECUTION,
                HookType.AFTER_TOOL_EXECUTION,
                HookType.ON_TOOL_ERROR,
                HookType.ON_SCAFFOLD_OPERATION_COMPLETED,
                HookType.CONTEXT_AFTER_CHANGE
            ])

    async def _process_with_events(self):
        """
        Process agent message and emit events.

        Uses agent.astream() to get streaming chunks which triggers registered hooks,
        which in turn emit events to the queue.
        """
        try:
            # Emit Idle event (agent ready to process)
            from . import agent as agent_events
            await self._enqueue(agent_events.Idle(metadata={'agent_id': self.agent.agent_id}))

            # Process message through agent streaming (hooks will fire and emit events)
            # Use astream to get content chunks that fire ON_CONTENT_CHUNK hooks
            result = None
            chunk_count = 0
            async for chunk in self.agent.astream(self.message):
                chunk_count += 1

                # Set execution_id from controller after streaming starts
                if self._execution_id is None:
                    self._execution_id = getattr(self.agent.controller, 'execution_id', None)

                # Chunks are processed by hooks which emit events
                # Store last chunk for metadata extraction
                result = chunk


            # Emit Done event
            await self._enqueue(agent_events.Done(
                interrupted=False,
                usage=result.metadata.get('usage') if hasattr(result, 'metadata') and result else None,
                finish_reason=result.metadata.get('finish_reason') if hasattr(result, 'metadata') and result else None,
                metadata={'agent_id': self.agent.agent_id}
            ))

        except asyncio.CancelledError:
            # Task was cancelled via stream.cancel() - Done(interrupted=True) is emitted by cancel() method
            # Don't emit another event, just re-raise to propagate cancellation
            raise

        except Exception as e:
            # Emit Error event
            from . import agent as agent_events
            await self._enqueue(agent_events.Error(
                message=str(e),
                detail={'exception_type': type(e).__name__},
                metadata={'agent_id': self.agent.agent_id}
            ))

        finally:
            self._finished = True

    async def _emit_content_chunk(self, chunk: Any, context: Any):
        """Convert streaming chunk to events.stream.ContentChunk.

        Note: ON_STREAMING_CHUNK hooks receive (chunk, context) not StreamExecContext.
        """
        # Filter by execution_id to avoid cross-stream events
        execution_id = getattr(self.agent.controller, 'execution_id', None)
        if self._execution_id is not None and execution_id != self._execution_id:
            return

        from . import stream

        # Extract text from chunk
        text = ""
        if isinstance(chunk, dict):
            text = chunk.get('delta', chunk.get('content', ''))
        elif hasattr(chunk, 'delta'):
            text = chunk.delta
        elif hasattr(chunk, 'content'):
            text = chunk.content
        else:
            text = str(chunk)

        event = stream.ContentChunk(
            text=text,
            sequence=getattr(chunk, 'sequence', 0),
            metadata={
                'agent_id': self.agent.agent_id,
                'execution_id': self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_tool_start(self, context: ToolExecContext):
        """Convert tool context to events.tool.Start.

        Note: Tool tasks may not have execution_id set, so we don't filter by it.
        Tools are executed asynchronously and their context may be created separately.
        Handles both ToolExecContext and BaseExecContext (from BEFORE_TOOL_EXECUTION).
        """
        from . import tool

        # Extract tool info - may be in context directly or in metadata
        tool_name = getattr(context, 'tool_name', None)
        tool_params = getattr(context, 'tool_params', None)

        # Fallback to metadata if direct attributes not available (BaseExecContext case)
        if tool_name is None and hasattr(context, 'metadata') and context.metadata:
            tool_names = context.metadata.get('tool_names', [])
            tool_name = tool_names[0] if tool_names else 'unknown'

        if tool_params is None:
            tool_params = {}

        event = tool.Start(
            tool_name=tool_name or 'unknown',
            params=tool_params,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None) or self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_tool_done(self, context: ToolExecContext):
        """Convert tool context to events.tool.Done.

        Note: Tool tasks may not have execution_id set, so we don't filter by it.
        Handles both ToolExecContext and BaseExecContext (from AFTER_TOOL_EXECUTION).
        """
        from . import tool

        # Extract tool info - may be in context directly or in metadata
        tool_name = getattr(context, 'tool_name', None)
        tool_result = getattr(context, 'tool_result', None)
        execution_time = getattr(context, 'execution_time', None)

        # Fallback to metadata if direct attributes not available (BaseExecContext case)
        if tool_name is None and hasattr(context, 'metadata') and context.metadata:
            tool_names = context.metadata.get('tool_names', [])
            tool_name = tool_names[0] if tool_names else 'unknown'

        event = tool.Done(
            tool_name=tool_name or 'unknown',
            result=tool_result,
            execution_time=execution_time,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None) or self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_tool_error(self, context: ToolExecContext):
        """Convert tool context to events.tool.Error.

        Note: Tool tasks may not have execution_id set, so we don't filter by it.
        Handles both ToolExecContext and BaseExecContext (from ON_TOOL_ERROR).
        """
        from . import tool

        # Extract tool info - may be in context directly or in metadata
        tool_name = getattr(context, 'tool_name', None)
        error = getattr(context, 'error', None)

        # Fallback to metadata if direct attributes not available (BaseExecContext case)
        if tool_name is None and hasattr(context, 'metadata') and context.metadata:
            tool_names = context.metadata.get('tool_names', [])
            tool_name = tool_names[0] if tool_names else 'unknown'

        event = tool.Error(
            tool_name=tool_name or 'unknown',
            error=error or Exception('Unknown error'),
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None) or self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_scaffold_complete(self, context: ScaffoldExecContext):
        """Convert scaffold context to events.scaffold.OpComplete."""
        if getattr(context, 'execution_id', None) != self._execution_id:
            return

        from . import scaffold
        event = scaffold.OpComplete(
            scaffold_type=context.scaffold_type,
            scaffold_id=context.scaffold_id,
            operation=context.operation_name,
            result=context.operation_result,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': context.execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_context_updated(self, context: ContextExecContext):
        """Convert context context to events.context.Updated."""
        # Don't filter by execution_id for context events - they may happen outside execution scope
        from . import context as context_events
        event = context_events.Updated(
            operation_type=context.operation_type,
            selector=context.selector,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None)
            }
        )
        await self._enqueue(event)

    async def _emit_tool_call_pre(self, context: ToolExecContext):
        """Convert tool context to events.tool.CallPre.

        Emitted from BEFORE_TOOL_CALL hook for individual tool calls.
        """
        from . import tool
        event = tool.CallPre(
            tool_name=context.tool_name,
            params=context.tool_params,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None) or self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_tool_call_post(self, context: ToolExecContext):
        """Convert tool context to events.tool.CallPost.

        Emitted from AFTER_TOOL_CALL hook for individual tool calls.
        """
        from . import tool
        event = tool.CallPost(
            tool_name=context.tool_name,
            result=context.tool_result,
            metadata={
                'agent_id': context.agent_id,
                'execution_id': getattr(context, 'execution_id', None) or self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_tool_detected(self, context: Any):
        """Convert streaming context to events.stream.ToolDetected.

        Emitted from ON_TOOL_CALL_DETECTED hook during streaming.
        """
        from . import stream

        # Extract tool info from context
        tool_name = 'unknown'
        call_id = 'unknown'

        # Check for tool_name direct attribute
        if hasattr(context, 'tool_name'):
            tool_name = context.tool_name
        # Check for chunk_data dict (StreamExecContext pattern)
        elif hasattr(context, 'chunk_data') and isinstance(context.chunk_data, dict):
            tool_name = context.chunk_data.get('tool_name', 'unknown')
            call_id = context.chunk_data.get('tool_call_id', 'unknown')
        # Check for tool_calls list
        elif hasattr(context, 'tool_calls') and context.tool_calls:
            # Get first tool call
            first_call = context.tool_calls[0]
            if hasattr(first_call, 'function') and hasattr(first_call.function, 'name'):
                tool_name = first_call.function.name
            if hasattr(first_call, 'id'):
                call_id = first_call.id

        event = stream.ToolDetected(
            tool_name=tool_name,
            call_id=call_id,
            metadata={
                'agent_id': self.agent.agent_id,
                'execution_id': self._execution_id
            }
        )
        await self._enqueue(event)

    async def _emit_scaffold_state_change(self, context: ScaffoldExecContext):
        """Convert scaffold context to events.scaffold.StateChange.

        Emitted from ON_SCAFFOLD_STATE_CHANGE hook.
        """
        if getattr(context, 'execution_id', None) != self._execution_id:
            return

        from . import scaffold
        event = scaffold.StateChange(
            scaffold_type=context.scaffold_type,
            scaffold_id=context.scaffold_id,
            changed_fields=context.changed_fields or [],
            snapshot=context.snapshot or {},
            metadata={
                'agent_id': context.agent_id,
                'execution_id': context.execution_id
            }
        )
        await self._enqueue(event)

    async def _enqueue(self, event):
        """
        Enqueue event with coalescing for streaming chunks.

        Args:
            event: Event dataclass to enqueue
        """
        try:
            await self.event_queue.put(event)
        except asyncio.QueueFull:
            # Coalesce streaming chunks if enabled
            from . import stream
            if self.coalesce_stream and isinstance(event, stream.ContentChunk):
                try:
                    # Drop oldest chunk
                    _ = self.event_queue.get_nowait()
                except Exception:
                    pass
                try:
                    await self.event_queue.put(event)
                except Exception:
                    pass
            # Never drop lifecycle/error events

    async def _cleanup_hooks(self):
        """Unregister temporary hooks."""
        hooks = self.agent._hooks_instance
        for hook_type in self._hook_cleanup:
            # Note: This assumes hooks.unregister_hook exists
            # May need to implement if not available
            if hasattr(hooks, 'unregister_hook'):
                hooks.unregister_hook(hook_type, self._emit_content_chunk)
                if self.verbose:
                    hooks.unregister_hook(hook_type, self._emit_tool_start)
                    hooks.unregister_hook(hook_type, self._emit_tool_done)
                    # etc.

    # Stream control methods

    async def send(self, message: str, **kwargs) -> None:
        """
        Send new message to agent.

        Args:
            message: New user message
            **kwargs: Additional parameters for agent.acall()
        """
        # Emit Idle event before processing new message
        from . import agent as agent_events
        await self._enqueue(agent_events.Idle(metadata={'agent_id': self.agent.agent_id}))

        # Process new message through agent streaming
        result = None
        async for chunk in self.agent.astream(message, **kwargs):
            # Update execution_id if needed
            if self._execution_id is None:
                self._execution_id = getattr(self.agent.controller, 'execution_id', None)
            result = chunk

        # Emit Done event for this message
        await self._enqueue(agent_events.Done(
            interrupted=False,
            usage=result.metadata.get('usage') if hasattr(result, 'metadata') and result else None,
            finish_reason=result.metadata.get('finish_reason') if hasattr(result, 'metadata') and result else None,
            metadata={'agent_id': self.agent.agent_id}
        ))

    async def cancel(self) -> None:
        """Cancel the current turn and emit Done(interrupted=True)."""
        try:
            # Cancel the processing task if it's running
            if self._processing_task and not self._processing_task.done():
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass  # Expected cancellation
                except Exception as e:
                    logger.warning(f"Unexpected error during task cancellation: {e}")

            # Cancel tool operations
            if hasattr(self.agent, '_task_loop') and self.agent._task_loop:
                await self.agent._task_loop.cancel_all_operations()

            # End streaming
            if hasattr(self.agent, '_streaming_orchestrator') and self.agent._streaming_orchestrator:
                if hasattr(self.agent._streaming_orchestrator, 'end_turn'):
                    await self.agent._streaming_orchestrator.end_turn()

            # Emit interrupted Done event
            from . import agent as agent_events
            await self._enqueue(agent_events.Done(
                interrupted=True,
                metadata={'agent_id': self.agent.agent_id}
            ))

        finally:
            self._finished = True

    async def context(self, action: str, **kwargs) -> None:
        """
        Update context.

        Args:
            action: Context action (dispatch, update, etc.)
            **kwargs: Action parameters
        """
        # Route to appropriate context method based on action
        if action == "dispatch":
            # Call context dispatch
            if hasattr(self.agent, 'context') and hasattr(self.agent.context, 'dispatch'):
                await self.agent.context.dispatch(**kwargs)
        elif action == "update":
            # Call context update
            if hasattr(self.agent, 'context') and hasattr(self.agent.context, 'update'):
                await self.agent.context.update(**kwargs)
        else:
            # Generic context operation - try to call the method by name
            if hasattr(self.agent, 'context'):
                method = getattr(self.agent.context, action, None)
                if method and callable(method):
                    if asyncio.iscoroutinefunction(method):
                        await method(**kwargs)
                    else:
                        method(**kwargs)

    async def scaffold_exec(self, name: str, operation: str, **params) -> Any:
        """
        Execute scaffold operation.

        Args:
            name: Scaffold name
            operation: Operation name
            **params: Operation parameters

        Returns:
            Operation result
        """
        # Access scaffold by name and execute operation
        if not hasattr(self.agent, 'scaffolds'):
            raise AttributeError(f"Agent does not have scaffolds")

        scaffold = getattr(self.agent.scaffolds, name, None)
        if scaffold is None:
            raise ValueError(f"Scaffold '{name}' not found on agent")

        operation_method = getattr(scaffold, operation, None)
        if operation_method is None:
            raise ValueError(f"Operation '{operation}' not found on scaffold '{name}'")

        if not callable(operation_method):
            raise ValueError(f"'{operation}' on scaffold '{name}' is not callable")

        # Execute the operation (may be sync or async)
        if asyncio.iscoroutinefunction(operation_method):
            result = await operation_method(**params)
        else:
            result = operation_method(**params)

        return result
