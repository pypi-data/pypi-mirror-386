"""
Agent lifecycle event dataclasses.

Events for agent lifecycle:
- Idle: Agent is ready for input
- Done: Agent turn completed
- Error: Agent error occurred
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Idle:
    """
    Agent is ready for input event.

    Emitted when agent is idle and waiting for next message.
    """
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Done:
    """
    Agent turn completed event.

    Emitted when agent finishes processing a turn.
    """
    interrupted: bool = False
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Error:
    """
    Agent error occurred event.

    Emitted when agent encounters a top-level error.
    """
    message: str
    detail: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
