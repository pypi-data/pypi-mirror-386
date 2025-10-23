"""
Agent Event API - Hierarchical event structure mirroring hook system.

Usage:
    from egregore.core.agent import events

    match event:
        case events.tool.Start(tool_name=name):
            ...
        case events.stream.ContentChunk(text=t):
            ...
        case events.scaffold.StateChange(changed_fields=fields):
            ...

Event Categories:
- events.tool.*      - Tool execution lifecycle
- events.stream.*    - Streaming chunks and tool detection
- events.scaffold.*  - Scaffold operations and state changes
- events.context.*   - Context operations
- events.agent.*     - Agent lifecycle
"""

from . import tool
from . import stream
from . import scaffold
from . import context
from . import agent

__all__ = ['tool', 'stream', 'scaffold', 'context', 'agent']
