from __future__ import annotations

from .contracts import AgentContext, BaseAgent, ToolRegistry


class YoutubeAgent(BaseAgent):
    name = "youtube_agent"

    def run(
        self,
        *,
        payload: dict,
        query: str,
        tools: ToolRegistry,
        context: AgentContext,
    ) -> dict:
        action = str(payload.get("action", "")).strip().lower()
        wants_study = (
            action in {"study", "analyze", "phrase_study"}
            or payload.get("segments")
            or payload.get("target_lang")
            or "frase" in query.lower()
            or "study" in query.lower()
        )

        if wants_study:
            study_result = self._call_tool(
                tools=tools,
                context=context,
                step="youtube_transcript_study",
                tool_name="youtube_transcript_study",
                payload={
                    "video": payload.get("video"),
                    "url": payload.get("url"),
                    "video_id": payload.get("video_id"),
                    "segments": payload.get("segments"),
                    "source_lang": payload.get("source_lang"),
                    "preferred_lang": payload.get("preferred_lang"),
                    "target_lang": payload.get("target_lang"),
                    "timing_mode": payload.get("timing_mode"),
                    "max_phrases": payload.get("max_phrases"),
                    "max_words": payload.get("max_words"),
                },
            )
            return {
                "ok": study_result.ok,
                "mode": "study",
                "result": study_result.data if study_result.ok else None,
                "error": study_result.error if not study_result.ok else "",
            }

        if not (payload.get("video") or payload.get("url") or payload.get("video_id")):
            return {
                "ok": False,
                "mode": "transcript",
                "error": "Provide one of: 'video', 'url', or 'video_id'.",
            }

        transcript_result = self._call_tool(
            tools=tools,
            context=context,
            step="youtube_transcript",
            tool_name="youtube_transcript",
            payload={
                "video": payload.get("video"),
                "url": payload.get("url"),
                "video_id": payload.get("video_id"),
                "preferred_lang": payload.get("preferred_lang"),
                "timing_mode": payload.get("timing_mode"),
            },
        )
        return {
            "ok": transcript_result.ok,
            "mode": "transcript",
            "result": transcript_result.data if transcript_result.ok else None,
            "error": transcript_result.error if not transcript_result.ok else "",
        }

