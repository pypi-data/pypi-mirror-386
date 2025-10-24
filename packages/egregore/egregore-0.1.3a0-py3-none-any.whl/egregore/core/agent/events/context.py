"""
Context operation event dataclasses.

Events for context operations, mirroring agent.hooks.context.* structure:
- Updated: Context was updated
- Added: Component added to context
- Dispatched: Context notification dispatched
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Updated:
    """
    Context was updated event.

    Emitted from various context hooks:
    - HookType.CONTEXT_UPDATE
    - HookType.CONTEXT_AFTER_CHANGE
    """
    operation_type: str  # "add", "dispatch", "update", "insert", "delete"
    selector: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Added:
    """
    Component added to context event.

    Emitted from HookType.CONTEXT_ADD.
    Corresponds to @agent.hooks.context.on_add decorator.
    """
    selector: str
    component_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dispatched:
    """
    Context notification dispatched event.

    Emitted from HookType.CONTEXT_DISPATCH.
    Corresponds to @agent.hooks.context.on_dispatch decorator.
    """
    action: str
    metadata: Dict[str, Any] = field(default_factory=dict)
