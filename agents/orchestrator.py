from __future__ import annotations

from typing import Any
import uuid

from .contracts import AgentContext, ToolRegistry
from .router import IntentRouter
from .practice_agent import PracticeAgent
from .conversation_agent import ConversationAgent
from .youtube_agent import YoutubeAgent
from .progress_agent import ProgressAgent


class AgentOrchestrator:
    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools
        self.router = IntentRouter()
        self.agents = {
            "practice": PracticeAgent(),
            "conversation": ConversationAgent(),
            "youtube": YoutubeAgent(),
            "progress": ProgressAgent(),
        }

    def run(
        self,
        *,
        intent: str | None,
        query: str | None,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = payload or {}
        query = str(query or "")
        trace_id = uuid.uuid4().hex[:12]
        context = AgentContext(trace_id=trace_id)

        try:
            decision = self.router.resolve(intent=intent, query=query, payload=payload)
        except ValueError as exc:
            return {
                "ok": False,
                "trace_id": trace_id,
                "intent_requested": str(intent or "auto"),
                "intent_resolved": "",
                "route_reason": "invalid_intent",
                "agent": "",
                "result": None,
                "errors": [str(exc)],
                "warnings": [],
                "trace": [],
            }

        resolved = decision.intent
        agent = self.agents.get(resolved)
        if not agent:
            return {
                "ok": False,
                "trace_id": trace_id,
                "intent_requested": str(intent or "auto"),
                "intent_resolved": resolved,
                "route_reason": decision.reason,
                "agent": "",
                "result": None,
                "errors": [f"No agent configured for intent '{resolved}'."],
                "warnings": [],
                "trace": [],
            }

        output = agent.run(
            payload=payload,
            query=query,
            tools=self.tools,
            context=context,
        )
        ok = bool(output.get("ok", False))

        return {
            "ok": ok,
            "trace_id": trace_id,
            "intent_requested": str(intent or "auto"),
            "intent_resolved": resolved,
            "route_reason": decision.reason,
            "agent": agent.name,
            "result": output.get("result", output),
            "mode": output.get("mode", ""),
            "errors": context.errors + ([output.get("error")] if output.get("error") else []),
            "warnings": context.warnings,
            "trace": [event.to_dict() for event in context.trace],
        }

