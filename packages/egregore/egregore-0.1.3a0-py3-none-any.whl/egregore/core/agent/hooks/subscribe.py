"""
Subscribe API - Imperative Hook Binding (codename: Synapse).

Provides lightweight, imperative API to bind/unbind agent hooks without decorators.
This is a thin layer over the existing ToolExecutionHooks system.

Public API:
- agent.on(name: str, fn: Callable) -> str
- agent.subscribe(mapping: dict[str, Callable]) -> str
- agent.unsubscribe(sub_id: str) -> None
- agent.subscription(name_or_mapping, fn=None) -> SubscriptionContext

Example:
    # Single hook
    sub_id = agent.on("stream:chunk", lambda ctx: print(ctx.delta, end=""))
    await agent.acall("Hello")
    agent.unsubscribe(sub_id)

    # Bulk hooks
    group_id = agent.subscribe({
        "tool:pre_exec": on_tool_start,
        "tool:post_exec": on_tool_end,
    })
    agent.unsubscribe(group_id)

    # Context manager
    async with agent.subscription("stream:chunk", on_chunk):
        await agent.acall("Streaming...")
"""

import uuid
import logging
from typing import Callable, Dict, List, Tuple, Union, Optional
from difflib import get_close_matches

from egregore.core.agent.hooks.execution import HookType

logger = logging.getLogger(__name__)


# Friendly name to HookType mapping
NAME_TO_HOOKTYPE: Dict[str, HookType] = {
    # Streaming hooks
    "stream:chunk": HookType.ON_STREAMING_CHUNK,
    "stream:tool_detect": HookType.ON_TOOL_CALL_DETECTED,
    "stream:content": HookType.ON_CONTENT_CHUNK,
    "stream:tool_start": HookType.ON_TOOL_START_CHUNK,
    "stream:tool_delta": HookType.ON_TOOL_DELTA_CHUNK,
    "stream:tool_complete": HookType.ON_TOOL_COMPLETE_CHUNK,
    "stream:tool_result": HookType.ON_TOOL_RESULT_CHUNK,

    # Tool execution hooks
    "tool:pre_exec": HookType.BEFORE_TOOL_EXECUTION,
    "tool:post_exec": HookType.ON_TOOL_TASK_COMPLETED,  # Maps to ToolTaskLoop's completion hook
    "tool:pre_call": HookType.BEFORE_TOOL_CALL,
    "tool:post_call": HookType.AFTER_TOOL_CALL,
    "tool:on_error": HookType.ON_TOOL_ERROR,
    "tool:intercept": HookType.CALL_INTERCEPT,

    # Context operation hooks
    "context:before_change": HookType.CONTEXT_BEFORE_CHANGE,
    "context:after_change": HookType.CONTEXT_AFTER_CHANGE,
    "context:on_add": HookType.CONTEXT_ADD,
    "context:on_dispatch": HookType.CONTEXT_DISPATCH,
    "context:on_update": HookType.CONTEXT_UPDATE,

    # Message hooks
    "message:on_user": HookType.MESSAGE_USER_INPUT,
    "message:on_provider": HookType.MESSAGE_PROVIDER_RESPONSE,
    "message:on_error": HookType.MESSAGE_ERROR,

    # Scaffold hooks
    "scaffold:op_complete": HookType.ON_SCAFFOLD_OPERATION_COMPLETED,
    "scaffold:state_change": HookType.ON_SCAFFOLD_STATE_CHANGE,
}


def resolve_hook_type(name: str) -> HookType:
    """
    Resolve friendly name to HookType enum.

    Args:
        name: Friendly name like "stream:chunk" or "tool:pre_exec"

    Returns:
        HookType enum value

    Raises:
        ValueError: If name is unknown, with suggestions for close matches
    """
    if name not in NAME_TO_HOOKTYPE:
        # Provide helpful suggestions
        all_names = list(NAME_TO_HOOKTYPE.keys())
        suggestions = get_close_matches(name, all_names, n=3, cutoff=0.6)

        error_msg = f"Unknown hook name: '{name}'"
        if suggestions:
            error_msg += f"\n\nDid you mean one of these?\n  - " + "\n  - ".join(suggestions)
        else:
            error_msg += f"\n\nAvailable hook names:\n  - " + "\n  - ".join(sorted(all_names))

        raise ValueError(error_msg)

    return NAME_TO_HOOKTYPE[name]


def _new_sub_id(prefix: str = "sub") -> str:
    """
    Generate unique subscription ID.

    Args:
        prefix: Prefix for the ID (default: "sub")

    Returns:
        Unique subscription ID like "sub_a7f3c2d1"
    """
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class _SubscriptionContext:
    """
    Context manager for temporary hook subscriptions.

    Automatically unsubscribes on exit. Supports both sync and async usage.
    """

    def __init__(self, agent, sub_id: str):
        """
        Initialize subscription context.

        Args:
            agent: Agent instance
            sub_id: Subscription ID to manage
        """
        self._agent = agent
        self._sub_id = sub_id
        self._unsubscribed = False

    @property
    def id(self) -> str:
        """Get subscription ID."""
        return self._sub_id

    def unsubscribe(self):
        """Manually unsubscribe (for early teardown)."""
        if not self._unsubscribed:
            self._agent.unsubscribe(self._sub_id)
            self._unsubscribed = True

    # Sync context manager
    def __enter__(self):
        """Enter sync context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context and auto-unsubscribe."""
        self.unsubscribe()
        return False

    # Async context manager
    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and auto-unsubscribe."""
        self.unsubscribe()
        return False


class SubscriptionMixin:
    """
    Mixin for Agent to add subscribe API.

    This will be mixed into the Agent class to provide:
    - agent.on(name, fn) -> sub_id
    - agent.subscribe(mapping) -> group_id
    - agent.unsubscribe(sub_id) -> None
    - agent.subscription(name_or_mapping, fn=None) -> context manager
    """

    def _init_subscriptions(self):
        """
        Initialize subscription registry.

        Should be called from Agent.__init__.
        """
        self._hook_subscriptions: Dict[str, List[Tuple[HookType, Callable]]] = {}

    def on(self, name: str, fn: Callable) -> str:
        """
        Register a single hook by friendly name.

        Args:
            name: Friendly hook name (e.g., "stream:chunk", "tool:pre_exec")
            fn: Callback function (sync or async)

        Returns:
            Subscription ID for later unsubscription

        Raises:
            ValueError: If name is unknown
            TypeError: If fn is not callable

        Example:
            sub_id = agent.on("stream:chunk", lambda ctx: print(ctx.delta))
            await agent.acall("Hello")
            agent.unsubscribe(sub_id)
        """
        # Validate callable
        if not callable(fn):
            raise TypeError(f"Hook function must be callable, got {type(fn).__name__}")

        # Resolve friendly name to HookType
        hook_type = resolve_hook_type(name)

        # Generate unique subscription ID
        sub_id = _new_sub_id()

        # Register hook with ToolExecutionHooks
        self._hooks_instance._register_hook(hook_type, fn)

        # Track in subscription registry
        if sub_id not in self._hook_subscriptions:
            self._hook_subscriptions[sub_id] = []
        self._hook_subscriptions[sub_id].append((hook_type, fn))

        logger.debug(f"Registered hook '{name}' -> {hook_type} with subscription ID: {sub_id}")

        return sub_id

    def subscribe(self, mapping: Dict[str, Callable]) -> str:
        """
        Register multiple hooks at once.

        Args:
            mapping: Dictionary of {friendly_name: callback_function}

        Returns:
            Group subscription ID for unsubscribing all at once

        Raises:
            ValueError: If any name is unknown
            TypeError: If any value is not callable

        Example:
            group_id = agent.subscribe({
                "stream:chunk": on_chunk,
                "tool:pre_exec": on_tool_start,
                "tool:post_exec": on_tool_end,
            })
            agent.unsubscribe(group_id)
        """
        # Generate group ID
        group_id = _new_sub_id(prefix="group")

        # Initialize group registry
        self._hook_subscriptions[group_id] = []

        # Register each hook and track under group ID
        for name, fn in mapping.items():
            # Validate callable
            if not callable(fn):
                raise TypeError(f"Hook function for '{name}' must be callable, got {type(fn).__name__}")

            # Resolve and register
            hook_type = resolve_hook_type(name)
            self._hooks_instance._register_hook(hook_type, fn)

            # Track under group ID
            self._hook_subscriptions[group_id].append((hook_type, fn))

        logger.debug(f"Registered {len(mapping)} hooks with group ID: {group_id}")

        return group_id

    def unsubscribe(self, sub_id: str) -> None:
        """
        Unregister subscription (single or group).

        Idempotent - safe to call multiple times or with non-existent IDs.

        Args:
            sub_id: Subscription ID returned from on() or subscribe()

        Example:
            sub_id = agent.on("stream:chunk", on_chunk)
            agent.unsubscribe(sub_id)
            agent.unsubscribe(sub_id)  # Safe - no error
        """
        if sub_id not in self._hook_subscriptions:
            # Idempotent - already unsubscribed or never existed
            logger.debug(f"Subscription {sub_id} not found (already unsubscribed or never existed)")
            return

        # Get all hooks registered under this ID
        hooks_to_remove = self._hook_subscriptions[sub_id]

        # Unregister each hook
        for hook_type, fn in hooks_to_remove:
            self._hooks_instance._unregister_hook(hook_type, fn)

        # Remove from registry
        del self._hook_subscriptions[sub_id]

        logger.debug(f"Unsubscribed {len(hooks_to_remove)} hooks for ID: {sub_id}")

    def subscription(
        self,
        name_or_mapping: Union[str, Dict[str, Callable]],
        fn: Optional[Callable] = None
    ) -> _SubscriptionContext:
        """
        Create context manager for temporary hook subscription.

        Automatically unsubscribes on exit. Supports both sync and async usage.

        Args:
            name_or_mapping: Either a friendly name (str) or a mapping dict
            fn: Callback function (required if name_or_mapping is str)

        Returns:
            Context manager that auto-unsubscribes

        Example:
            # Single hook
            async with agent.subscription("stream:chunk", on_chunk):
                await agent.acall("Streaming...")

            # Multiple hooks
            with agent.subscription({
                "tool:pre_exec": on_start,
                "tool:post_exec": on_end,
            }):
                result = agent.call("Execute with policies")
        """
        # Determine if single or bulk subscription
        if isinstance(name_or_mapping, str):
            # Single hook - fn is required
            if fn is None:
                raise ValueError("Callback function 'fn' is required when using single hook name")
            sub_id = self.on(name_or_mapping, fn)
        elif isinstance(name_or_mapping, dict):
            # Bulk subscription
            sub_id = self.subscribe(name_or_mapping)
        else:
            raise TypeError(
                f"First argument must be str (hook name) or dict (mapping), "
                f"got {type(name_or_mapping).__name__}"
            )

        return _SubscriptionContext(self, sub_id)
