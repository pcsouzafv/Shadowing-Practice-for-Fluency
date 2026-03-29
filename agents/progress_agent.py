from __future__ import annotations

from .contracts import AgentContext, BaseAgent, ToolRegistry


def _build_progress_summary(entries: list[dict]) -> dict:
    total_sessions = len(entries)
    total_minutes = sum(int(item.get("duration_min") or 0) for item in entries)
    avg_difficulty = (
        round(sum(int(item.get("difficulty") or 0) for item in entries) / total_sessions, 2)
        if total_sessions else 0.0
    )
    last_session = entries[-1]["date"] if entries and entries[-1].get("date") else ""
    return {
        "sessions": total_sessions,
        "minutes": total_minutes,
        "avg_difficulty": avg_difficulty,
        "last_session": last_session,
    }


class ProgressAgent(BaseAgent):
    name = "progress_agent"

    def run(
        self,
        *,
        payload: dict,
        query: str,
        tools: ToolRegistry,
        context: AgentContext,
    ) -> dict:
        action = str(payload.get("action", "")).strip().lower()

        if action == "save" or any(
            k in payload for k in ("duration_min", "repetitions", "difficulty", "material", "notes")
        ):
            save_result = self._call_tool(
                tools=tools,
                context=context,
                step="save_progress",
                tool_name="progress_save",
                payload={
                    "date": payload.get("date"),
                    "material": payload.get("material"),
                    "duration_min": payload.get("duration_min"),
                    "repetitions": payload.get("repetitions"),
                    "difficulty": payload.get("difficulty"),
                    "notes": payload.get("notes"),
                    "learner_key": payload.get("learner_key"),
                    "learner_name": payload.get("learner_name"),
                    "learner_level": payload.get("learner_level") or payload.get("level"),
                    "lang": payload.get("lang"),
                },
            )
            return {
                "ok": save_result.ok,
                "mode": "save",
                "result": save_result.data if save_result.ok else None,
                "error": save_result.error if not save_result.ok else "",
            }

        # Default mode: summary/list
        list_result = self._call_tool(
            tools=tools,
            context=context,
            step="get_progress",
            tool_name="progress_get",
            payload={
                "learner_key": payload.get("learner_key"),
                "learner_name": payload.get("learner_name"),
                "learner_level": payload.get("learner_level") or payload.get("level"),
                "lang": payload.get("lang"),
            },
        )
        if not list_result.ok:
            return {
                "ok": False,
                "mode": "summary",
                "error": list_result.error,
            }

        entries = list_result.data if isinstance(list_result.data, list) else []
        return {
            "ok": True,
            "mode": "summary",
            "result": {
                "summary": _build_progress_summary(entries),
                "entries": entries[-20:],
            },
        }
