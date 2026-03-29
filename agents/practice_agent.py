from __future__ import annotations

from .contracts import AgentContext, BaseAgent, ToolRegistry


class PracticeAgent(BaseAgent):
    name = "practice_agent"

    def run(
        self,
        *,
        payload: dict,
        query: str,
        tools: ToolRegistry,
        context: AgentContext,
    ) -> dict:
        action = str(payload.get("action", "")).strip().lower()

        if action in {"generate_practice_text", "practice_text", "generate_text"}:
            mode = "generate_practice_text"
            res = self._call_tool(
                tools=tools,
                context=context,
                step="generate_practice_text",
                tool_name="generate_practice_text",
                payload={
                    "topic": payload.get("topic"),
                    "level": payload.get("level"),
                    "focus": payload.get("focus"),
                    "target_lang": payload.get("target_lang"),
                    "text_length": payload.get("text_length"),
                    "text_type": payload.get("text_type"),
                    "learner_key": payload.get("learner_key"),
                    "learner_name": payload.get("learner_name"),
                    "learner_level": payload.get("learner_level") or payload.get("level"),
                },
            )
            return {
                "ok": res.ok,
                "mode": mode,
                "result": res.data if res.ok else None,
                "error": res.error if not res.ok else "",
            }

        if action in {"analyze", "analysis"}:
            mode = "analyze_only"
            if not payload.get("text"):
                return {"ok": False, "mode": mode, "error": "Field 'text' is required for analysis."}
            res = self._call_tool(
                tools=tools,
                context=context,
                step="analyze_text",
                tool_name="analyze_text",
                payload={
                    "text": payload.get("text"),
                    "lang": payload.get("lang"),
                    "learner_key": payload.get("learner_key"),
                    "learner_name": payload.get("learner_name"),
                    "learner_level": payload.get("learner_level") or payload.get("level"),
                },
            )
            return {
                "ok": res.ok,
                "mode": mode,
                "result": res.data if res.ok else None,
                "error": res.error if not res.ok else "",
            }

        # Default mode: full practice session from text.
        if not payload.get("text"):
            return {
                "ok": False,
                "mode": "session",
                "error": "Field 'text' is required to generate a practice session.",
            }

        session_result = self._call_tool(
            tools=tools,
            context=context,
            step="generate_session",
            tool_name="generate_session",
            payload={
                "text": payload.get("text"),
                "lang": payload.get("lang"),
                "voice": payload.get("voice"),
                "tts_engine": payload.get("tts_engine"),
                "use_lmnt": payload.get("use_lmnt"),
                "learner_key": payload.get("learner_key"),
                "learner_name": payload.get("learner_name"),
                "learner_level": payload.get("learner_level") or payload.get("level"),
            },
        )
        if not session_result.ok:
            return {
                "ok": False,
                "mode": "session",
                "error": session_result.error,
            }

        output = {
            "ok": True,
            "mode": "session",
            "session": session_result.data,
        }

        analyze_requested = bool(payload.get("analyze")) or ("analisar" in query.lower())
        if analyze_requested:
            analysis_result = self._call_tool(
                tools=tools,
                context=context,
                step="analyze_text",
                tool_name="analyze_text",
                payload={
                    "text": payload.get("text"),
                    "lang": payload.get("lang"),
                    "learner_key": payload.get("learner_key"),
                    "learner_name": payload.get("learner_name"),
                    "learner_level": payload.get("learner_level") or payload.get("level"),
                },
                note="optional_analysis_after_session",
            )
            if analysis_result.ok:
                output["analysis"] = analysis_result.data
            else:
                context.warnings.append(
                    "Practice session succeeded, but analysis tool failed."
                )
                output["analysis_error"] = analysis_result.error

        return output
