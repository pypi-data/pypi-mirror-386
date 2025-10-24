"""
Streaming event dataclasses.

Events for streaming chunks and tool detection, mirroring agent.hooks.streaming.* structure:
- ContentChunk: Content chunk from streaming response
- ToolChunk: Tool-related streaming chunk
- ToolDetected: Tool call detected during streaming
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ContentChunk:
    """
    Content chunk from streaming response.

    Emitted from HookType.ON_CONTENT_CHUNK.
    Corresponds to @agent.hooks.streaming.on_content decorator.
    """
    text: str
    sequence: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolChunk:
    """
    Tool-related chunk during streaming.

    Emitted from various tool streaming hooks:
    - HookType.ON_TOOL_START_CHUNK
    - HookType.ON_TOOL_DELTA_CHUNK
    - HookType.ON_TOOL_COMPLETE_CHUNK
    - HookType.ON_TOOL_RESULT_CHUNK
    """
    chunk_type: str  # "tool_start", "tool_delta", "tool_complete", "tool_result"
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDetected:
    """
    Tool call detected during streaming.

    Emitted from HookType.ON_TOOL_CALL_DETECTED.
    Corresponds to @agent.hooks.streaming.tool_detection decorator.
    """
    tool_name: str
    call_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
