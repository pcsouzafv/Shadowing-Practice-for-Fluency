from __future__ import annotations

from dataclasses import dataclass


VALID_INTENTS = {"auto", "practice", "conversation", "youtube", "progress"}


@dataclass
class RouteDecision:
    intent: str
    reason: str


class IntentRouter:
    def resolve(
        self,
        intent: str | None,
        query: str | None,
        payload: dict | None,
    ) -> RouteDecision:
        payload = payload or {}
        query_lc = str(query or "").strip().lower()
        requested = str(intent or "auto").strip().lower() or "auto"

        if requested not in VALID_INTENTS:
            raise ValueError(
                f"Invalid intent '{requested}'. Use one of: {', '.join(sorted(VALID_INTENTS))}."
            )
        if requested != "auto":
            return RouteDecision(intent=requested, reason="explicit_intent")

        # Payload-first routing
        if any(key in payload for key in ("audio_b64", "history", "lesson_focus", "translate_to")):
            return RouteDecision(intent="conversation", reason="payload_conversation_keys")
        if any(key in payload for key in ("video", "video_id", "url", "segments", "timing_mode")):
            return RouteDecision(intent="youtube", reason="payload_youtube_keys")
        if any(key in payload for key in ("duration_min", "repetitions", "difficulty", "material", "notes")):
            return RouteDecision(intent="progress", reason="payload_progress_keys")
        if any(
            key in payload
            for key in ("text", "topic", "text_length", "text_type", "target_lang", "tts_engine")
        ):
            return RouteDecision(intent="practice", reason="payload_practice_keys")

        # Query keyword routing
        if query_lc:
            if any(k in query_lc for k in ("youtube", "karaoke", "transcript", "legenda", "video")):
                return RouteDecision(intent="youtube", reason="query_youtube_keywords")
            if any(k in query_lc for k in ("convers", "voice", "chat", "dialog", "lesson", "correction")):
                return RouteDecision(intent="conversation", reason="query_conversation_keywords")
            if any(k in query_lc for k in ("progress", "streak", "history", "log", "csv", "metrics")):
                return RouteDecision(intent="progress", reason="query_progress_keywords")
            if any(k in query_lc for k in ("practice", "shadow", "analy", "análise", "texto")):
                return RouteDecision(intent="practice", reason="query_practice_keywords")

        return RouteDecision(intent="practice", reason="fallback_default_practice")

