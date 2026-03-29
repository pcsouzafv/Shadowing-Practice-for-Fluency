from __future__ import annotations

from .contracts import AgentContext, BaseAgent, ToolRegistry


class ConversationAgent(BaseAgent):
    name = "conversation_agent"

    def run(
        self,
        *,
        payload: dict,
        query: str,
        tools: ToolRegistry,
        context: AgentContext,
    ) -> dict:
        action = str(payload.get("action", "")).strip().lower()

        if action in {"turn", "chat", "speak"} or payload.get("audio_b64"):
            if not payload.get("audio_b64"):
                return {"ok": False, "mode": "turn", "error": "Field 'audio_b64' is required."}
            turn_result = self._call_tool(
                tools=tools,
                context=context,
                step="conversation_turn",
                tool_name="conversation_turn",
                payload={
                    "audio_b64": payload.get("audio_b64"),
                    "lang": payload.get("lang"),
                    "voice": payload.get("voice"),
                    "history": payload.get("history"),
                    "tts_engine": payload.get("tts_engine"),
                    "use_lmnt": payload.get("use_lmnt"),
                    "suggest": payload.get("suggest"),
                    "learner_key": payload.get("learner_key"),
                    "learner_name": payload.get("learner_name"),
                    "learner_level": payload.get("learner_level") or payload.get("level"),
                },
            )
            return {
                "ok": turn_result.ok,
                "mode": "turn",
                "result": turn_result.data if turn_result.ok else None,
                "error": turn_result.error if not turn_result.ok else "",
            }

        # Default: lesson generation from chat history.
        if not payload.get("history"):
            return {
                "ok": False,
                "mode": "lesson",
                "error": "Field 'history' is required for conversation lesson.",
            }

        lesson_focus = payload.get("lesson_focus")
        if not lesson_focus and "corre" in query.lower():
            lesson_focus = "corrections"
        if not lesson_focus and "vocab" in query.lower():
            lesson_focus = "vocabulary"
        if not lesson_focus:
            lesson_focus = "balanced"

        lesson_result = self._call_tool(
            tools=tools,
            context=context,
            step="conversation_lesson",
            tool_name="conversation_lesson",
            payload={
                "history": payload.get("history"),
                "lang": payload.get("lang"),
                "translate_to": payload.get("translate_to"),
                "lesson_focus": lesson_focus,
                "learner_key": payload.get("learner_key"),
                "learner_name": payload.get("learner_name"),
                "learner_level": payload.get("learner_level") or payload.get("level"),
            },
        )
        return {
            "ok": lesson_result.ok,
            "mode": "lesson",
            "result": lesson_result.data if lesson_result.ok else None,
            "error": lesson_result.error if not lesson_result.ok else "",
        }
