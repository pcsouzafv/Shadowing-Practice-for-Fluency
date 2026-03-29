from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import time


@dataclass
class ToolResult:
    ok: bool
    status_code: int
    data: Any = None
    error: str = ""
    tool: str = ""


@dataclass
class TraceEvent:
    step: str
    tool: str
    ok: bool
    status_code: int
    latency_ms: int
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "tool": self.tool,
            "ok": self.ok,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "note": self.note,
        }


@dataclass
class AgentContext:
    trace_id: str
    trace: list[TraceEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


ToolCallable = Callable[[dict[str, Any]], ToolResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, fn: ToolCallable) -> None:
        if not name:
            raise ValueError("Tool name cannot be empty.")
        self._tools[name] = fn

    def has(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, payload: dict[str, Any] | None = None) -> ToolResult:
        payload = payload or {}
        fn = self._tools.get(name)
        if not fn:
            return ToolResult(
                ok=False,
                status_code=404,
                error=f"Tool '{name}' is not registered.",
                tool=name,
            )
        try:
            result = fn(payload)
            if not isinstance(result, ToolResult):
                return ToolResult(
                    ok=False,
                    status_code=500,
                    error=f"Tool '{name}' returned invalid result type.",
                    tool=name,
                )
            result.tool = name
            return result
        except Exception as exc:  # defensive boundary for tool failures
            return ToolResult(
                ok=False,
                status_code=500,
                error=f"Tool '{name}' failed: {exc}",
                tool=name,
            )


class BaseAgent:
    name = "base_agent"

    def _call_tool(
        self,
        *,
        tools: ToolRegistry,
        context: AgentContext,
        step: str,
        tool_name: str,
        payload: dict[str, Any] | None = None,
        note: str = "",
    ) -> ToolResult:
        started = time.perf_counter()
        result = tools.call(tool_name, payload or {})
        latency_ms = int((time.perf_counter() - started) * 1000)
        context.trace.append(
            TraceEvent(
                step=step,
                tool=tool_name,
                ok=result.ok,
                status_code=result.status_code,
                latency_ms=latency_ms,
                note=note,
            )
        )
        if not result.ok and result.error:
            context.errors.append(result.error)
        return result

