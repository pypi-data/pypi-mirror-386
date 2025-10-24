"""
Scaffold operation event dataclasses.

Events for scaffold operations and state changes, mirroring agent.hooks.scaffold.* structure:
- OpStarted: Scaffold operation started
- OpComplete: Scaffold operation completed
- OpFailed: Scaffold operation failed
- StateChange: Scaffold state changed
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class OpStarted:
    """
    Scaffold operation started event.

    Emitted when scaffold operation begins execution.
    """
    scaffold_type: str
    scaffold_id: str
    operation: str
    params: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpComplete:
    """
    Scaffold operation completed event.

    Emitted from HookType.ON_SCAFFOLD_OPERATION_COMPLETED.
    Corresponds to @agent.hooks.scaffold.post decorator.
    """
    scaffold_type: str
    scaffold_id: str
    operation: str
    result: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpFailed:
    """
    Scaffold operation failed event.

    Emitted when scaffold operation encounters an error.
    """
    scaffold_type: str
    scaffold_id: str
    operation: str
    error: Exception
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateChange:
    """
    Scaffold state changed event.

    Emitted from HookType.ON_SCAFFOLD_STATE_CHANGE.
    Corresponds to @agent.hooks.scaffold.on_state_change decorator.
    """
    scaffold_type: str
    scaffold_id: str
    changed_fields: List[str]
    snapshot: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
