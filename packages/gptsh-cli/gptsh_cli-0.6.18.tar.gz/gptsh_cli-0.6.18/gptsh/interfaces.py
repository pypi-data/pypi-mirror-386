from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Protocol


class LLMClient(Protocol):
    async def complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a non-streaming completion and return the raw response."""

    async def stream(self, params: Dict[str, Any]) -> AsyncIterator[Any]:
        """Yield provider stream chunks (dicts/objects) or text deltas.

        The session layer is responsible for extracting text and handling tool-call
        deltas from raw provider chunks.
        """


class MCPClient(Protocol):
    async def start(self) -> None:
        """Initialize discovery and connections to MCP servers."""

    async def list_tools(self) -> Dict[str, List[str]]:
        """Return a mapping of server -> list of tool names."""

    async def call_tool(self, server: str, tool: str, args: Dict[str, Any]) -> str:
        """Invoke a tool and return its textual result."""

    async def stop(self) -> None:
        """Tear down connections/processes if needed."""


class ApprovalPolicy(Protocol):
    def is_auto_allowed(self, server: str, tool: str) -> bool:
        """Return True if the tool is auto-approved without interaction."""

    async def confirm(self, server: str, tool: str, args: Dict[str, Any]) -> bool:
        """Ask user for approval; return True if allowed."""


class ProgressReporter(Protocol):
    def start(self) -> None:  # pragma: no cover - simple pass-through
        ...

    def stop(self) -> None:  # pragma: no cover - simple pass-through
        ...

    def add_task(self, description: str) -> Optional[int]:
        """Create a task and return its id (or None if not supported)."""

    def complete_task(self, task_id: Optional[int], description: Optional[str] = None) -> None:
        """Mark a task as completed and optionally update its description."""

    def update_task(self, task_id: Optional[int], description: Optional[str] = None) -> None:
        """Update a task's description without completing it (no-op if unsupported)."""

    def remove_task(self, task_id: Optional[int]) -> None:
        """Remove a task from display (no-op if unsupported)."""

    def pause(self) -> None:  # pragma: no cover - UI concern
        ...

    def resume(self) -> None:  # pragma: no cover - UI concern
        ...

    # IO guards used throughout runner/session to prevent garbled output while spinners render
    def io(self):  # returns a context manager
        ...

    async def aio_io(self):  # returns an async context manager
        ...

    # Debounced per-task helpers used around MCP tool execution
    def start_debounced_task(self, description: str, delay: float = 0.1) -> int:
        ...

    def complete_debounced_task(self, handle: int, final_description: Optional[str] = None) -> None:
        ...

