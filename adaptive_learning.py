from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover - optional dependency
    psycopg = None
    dict_row = None


logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "postgresql://idiomasbr:idiomasbr123@localhost:5433/idiomasbr"
DISABLED_DATABASE_URLS = {"0", "false", "disable", "disabled", "none", "null", "off"}
SCHEMA_NAME = "shadowing_adaptive"
LEARNERS_TABLE = f"{SCHEMA_NAME}.learners"
PROGRESS_TABLE = f"{SCHEMA_NAME}.progress_entries"
EVENTS_TABLE = f"{SCHEMA_NAME}.learning_events"
REVIEW_TABLE = f"{SCHEMA_NAME}.review_items"
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean_text(value: Any, *, max_chars: int = 2000) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip()
    return text


def _normalize_lang(value: Any, default: str = "en") -> str:
    raw = _clean_text(value, max_chars=12).lower()
    if not raw:
        return default
    return raw.split("-", 1)[0] or default


def _normalize_key(value: Any, default: str = "web-default") -> str:
    raw = _clean_text(value, max_chars=120).lower()
    if not raw:
        return default
    normalized = re.sub(r"[^a-z0-9:_-]+", "-", raw).strip("-")
    return normalized or default


def _normalize_email(value: Any) -> str:
    return _clean_text(value, max_chars=254).lower()


def _normalize_phone(value: Any) -> str:
    raw = _clean_text(value, max_chars=32)
    if not raw:
        return ""
    digits = re.sub(r"[^\d+]+", "", raw)
    return digits[:32]


def _coerce_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        numeric = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return numeric if numeric > 0 else None


def _item_key(value: Any, *, fallback_prefix: str) -> str:
    cleaned = _clean_text(value, max_chars=220).lower()
    if cleaned:
        normalized = re.sub(r"[^a-z0-9à-öø-ÿ']+", "-", cleaned).strip("-")
        if normalized:
            return normalized[:160]
    return f"{fallback_prefix}-{_normalize_key(value, default='item')}"


def _score_ratio(score: Any) -> float:
    if score is None:
        return 0.55
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return 0.55
    if numeric > 1.0:
        numeric = numeric / 100.0
    return max(0.05, min(1.0, numeric))


def _round_score(score: Any) -> float | None:
    if score is None:
        return None
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return None
    if numeric <= 1.0:
        numeric = numeric * 100.0
    return round(max(1.0, min(100.0, numeric)), 1)


def _json_dumps(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value in (None, ""):
        return "{}"
    return json.dumps({"value": value}, ensure_ascii=False)


def _serialize_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    return ""


def _extract_phrase_tokens(text: str, *, limit: int = 12) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for token in TOKEN_RE.findall(text or ""):
        key = token.casefold()
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tokens


@dataclass(slots=True)
class LearnerContext:
    learner_key: str
    channel: str = "web"
    display_name: str = ""
    target_lang: str = "en"
    level: str = "A1"
    native_lang: str = "pt"
    source_system: str = "shadowing_practice"
    external_user_id: int | None = None
    external_email: str = ""
    external_phone: str = ""


class AdaptiveLearningStore:
    def __init__(self, database_url: str = "") -> None:
        raw_database_url = (database_url or os.getenv("DATABASE_URL", "") or DEFAULT_DATABASE_URL).strip()
        self.disabled_by_config = raw_database_url.lower() in DISABLED_DATABASE_URLS
        self.database_url = "" if self.disabled_by_config else raw_database_url
        self.enabled = bool(self.database_url and psycopg is not None)
        self.last_error = ""
        self._schema_ready = False

    def _safe_database_label(self) -> str:
        try:
            parsed = urlparse(self.database_url)
        except Exception:
            return ""
        if not parsed.scheme:
            return ""
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        name = parsed.path.strip("/") or "postgres"
        return f"{host}:{port}/{name}"

    def health(self) -> dict[str, Any]:
        status = {
            "enabled": self.enabled,
            "driver": bool(psycopg),
            "database": self._safe_database_label(),
            "schema_ready": self._schema_ready,
            "schema": SCHEMA_NAME,
            "identity_source": "public.users",
        }
        if self.last_error:
            status["last_error"] = self.last_error
        if not self.enabled:
            if self.disabled_by_config:
                status["reason"] = "database_disabled"
            elif not psycopg:
                status["reason"] = "psycopg_not_installed"
            elif not self.database_url:
                status["reason"] = "database_url_missing"
        return status

    def _connect(self):
        if not self.enabled or not psycopg:
            return None
        return psycopg.connect(
            self.database_url,
            autocommit=True,
            row_factory=dict_row,
        )

    def ensure_schema(self) -> bool:
        if not self.enabled:
            return False
        if self._schema_ready:
            return True
        try:
            with self._connect() as conn:
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {LEARNERS_TABLE} (
                        id BIGSERIAL PRIMARY KEY,
                        learner_key TEXT NOT NULL UNIQUE,
                        channel TEXT NOT NULL DEFAULT 'web',
                        display_name TEXT NOT NULL DEFAULT '',
                        native_lang TEXT NOT NULL DEFAULT 'pt',
                        target_lang TEXT NOT NULL DEFAULT 'en',
                        level TEXT NOT NULL DEFAULT 'A1',
                        source_system TEXT NOT NULL DEFAULT 'shadowing_practice',
                        external_user_id BIGINT,
                        external_email TEXT NOT NULL DEFAULT '',
                        external_phone TEXT NOT NULL DEFAULT '',
                        total_sessions INTEGER NOT NULL DEFAULT 0,
                        total_minutes INTEGER NOT NULL DEFAULT 0,
                        avg_difficulty NUMERIC(5,2) NOT NULL DEFAULT 0,
                        pronunciation_avg_score NUMERIC(5,2) NOT NULL DEFAULT 0,
                        pronunciation_samples INTEGER NOT NULL DEFAULT 0,
                        review_due_count INTEGER NOT NULL DEFAULT 0,
                        last_activity_at TIMESTAMPTZ,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                conn.execute(
                    f"ALTER TABLE {LEARNERS_TABLE} ADD COLUMN IF NOT EXISTS source_system TEXT NOT NULL DEFAULT 'shadowing_practice'"
                )
                conn.execute(
                    f"ALTER TABLE {LEARNERS_TABLE} ADD COLUMN IF NOT EXISTS external_user_id BIGINT"
                )
                conn.execute(
                    f"ALTER TABLE {LEARNERS_TABLE} ADD COLUMN IF NOT EXISTS external_email TEXT NOT NULL DEFAULT ''"
                )
                conn.execute(
                    f"ALTER TABLE {LEARNERS_TABLE} ADD COLUMN IF NOT EXISTS external_phone TEXT NOT NULL DEFAULT ''"
                )
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {PROGRESS_TABLE} (
                        id BIGSERIAL PRIMARY KEY,
                        learner_id BIGINT NOT NULL REFERENCES {LEARNERS_TABLE}(id) ON DELETE CASCADE,
                        entry_date DATE NOT NULL,
                        material TEXT NOT NULL DEFAULT '',
                        duration_min INTEGER NOT NULL DEFAULT 0,
                        repetitions INTEGER NOT NULL DEFAULT 0,
                        difficulty INTEGER NOT NULL DEFAULT 3,
                        notes TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {EVENTS_TABLE} (
                        id BIGSERIAL PRIMARY KEY,
                        learner_id BIGINT NOT NULL REFERENCES {LEARNERS_TABLE}(id) ON DELETE CASCADE,
                        event_type TEXT NOT NULL,
                        channel TEXT NOT NULL DEFAULT 'web',
                        target_lang TEXT NOT NULL DEFAULT 'en',
                        skill_area TEXT NOT NULL DEFAULT 'general',
                        score NUMERIC(6,2),
                        difficulty INTEGER,
                        duration_sec INTEGER,
                        content_ref TEXT NOT NULL DEFAULT '',
                        content_text TEXT NOT NULL DEFAULT '',
                        payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {REVIEW_TABLE} (
                        id BIGSERIAL PRIMARY KEY,
                        learner_id BIGINT NOT NULL REFERENCES {LEARNERS_TABLE}(id) ON DELETE CASCADE,
                        item_type TEXT NOT NULL,
                        item_key TEXT NOT NULL,
                        source_text TEXT NOT NULL,
                        target_lang TEXT NOT NULL DEFAULT 'en',
                        translation TEXT NOT NULL DEFAULT '',
                        context_text TEXT NOT NULL DEFAULT '',
                        skill_area TEXT NOT NULL DEFAULT 'general',
                        notes TEXT NOT NULL DEFAULT '',
                        mastery_score NUMERIC(5,2) NOT NULL DEFAULT 0.25,
                        interval_days INTEGER NOT NULL DEFAULT 0,
                        next_due_at TIMESTAMPTZ,
                        last_seen_at TIMESTAMPTZ,
                        last_result_score NUMERIC(6,2) NOT NULL DEFAULT 0,
                        seen_count INTEGER NOT NULL DEFAULT 0,
                        success_count INTEGER NOT NULL DEFAULT 0,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE (learner_id, item_type, item_key, target_lang)
                    )
                    """
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_progress_learner_date ON {PROGRESS_TABLE} (learner_id, entry_date DESC)"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_events_learner_created_at ON {EVENTS_TABLE} (learner_id, created_at DESC)"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_review_due ON {REVIEW_TABLE} (learner_id, next_due_at, mastery_score)"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_learners_external_user_id ON {LEARNERS_TABLE} (external_user_id)"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_learners_external_email ON {LEARNERS_TABLE} (lower(external_email))"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_shadowing_adaptive_learners_external_phone ON {LEARNERS_TABLE} (external_phone)"
                )
            self._schema_ready = True
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore schema init failed: %s", exc)
            return False

    def _resolve_system_user(self, conn, learner: LearnerContext) -> dict[str, Any] | None:
        external_user_id = _coerce_optional_int(learner.external_user_id)
        external_email = _normalize_email(learner.external_email)
        external_phone = _normalize_phone(learner.external_phone)

        if external_user_id:
            row = conn.execute(
                """
                SELECT id, email, name, phone_number
                FROM public.users
                WHERE id = %s
                """,
                (external_user_id,),
            ).fetchone()
            return dict(row) if row else None

        if external_email:
            row = conn.execute(
                """
                SELECT id, email, name, phone_number
                FROM public.users
                WHERE lower(email) = lower(%s)
                """,
                (external_email,),
            ).fetchone()
            return dict(row) if row else None

        if external_phone:
            row = conn.execute(
                """
                SELECT id, email, name, phone_number
                FROM public.users
                WHERE phone_number = %s
                """,
                (external_phone,),
            ).fetchone()
            return dict(row) if row else None

        return None

    def _find_learner_row(self, conn, learner: LearnerContext | str) -> dict[str, Any] | None:
        if isinstance(learner, str):
            row = conn.execute(
                f"SELECT * FROM {LEARNERS_TABLE} WHERE learner_key = %s",
                (_normalize_key(learner),),
            ).fetchone()
            return dict(row) if row else None

        system_user = self._resolve_system_user(conn, learner)
        if system_user:
            row = conn.execute(
                f"SELECT * FROM {LEARNERS_TABLE} WHERE external_user_id = %s",
                (system_user["id"],),
            ).fetchone()
            if row:
                return dict(row)

        row = conn.execute(
            f"SELECT * FROM {LEARNERS_TABLE} WHERE learner_key = %s",
            (_normalize_key(learner.learner_key),),
        ).fetchone()
        if row:
            return dict(row)

        if system_user:
            email = _normalize_email(system_user.get("email"))
            if email:
                row = conn.execute(
                    f"SELECT * FROM {LEARNERS_TABLE} WHERE lower(external_email) = lower(%s)",
                    (email,),
                ).fetchone()
                if row:
                    return dict(row)
            phone = _normalize_phone(system_user.get("phone_number"))
            if phone:
                row = conn.execute(
                    f"SELECT * FROM {LEARNERS_TABLE} WHERE external_phone = %s",
                    (phone,),
                ).fetchone()
                if row:
                    return dict(row)

        return None

    def _ensure_learner(self, conn, learner: LearnerContext) -> dict[str, Any]:
        learner_key = _normalize_key(learner.learner_key)
        target_lang = _normalize_lang(learner.target_lang, default="en")
        level = _clean_text(learner.level, max_chars=16) or "A1"
        display_name = _clean_text(learner.display_name, max_chars=120)
        native_lang = _normalize_lang(learner.native_lang, default="pt")
        channel = _clean_text(learner.channel, max_chars=24) or "web"
        source_system = _clean_text(learner.source_system, max_chars=40) or "shadowing_practice"
        system_user = self._resolve_system_user(conn, learner) or {}
        external_user_id = _coerce_optional_int(system_user.get("id") or learner.external_user_id)
        external_email = _normalize_email(system_user.get("email") or learner.external_email)
        external_phone = _normalize_phone(system_user.get("phone_number") or learner.external_phone)
        if not display_name:
            display_name = _clean_text(system_user.get("name"), max_chars=120)

        row = self._find_learner_row(conn, learner)
        if row:
            conn.execute(
                f"""
                UPDATE {LEARNERS_TABLE}
                SET channel = %s,
                    display_name = CASE WHEN %s <> '' THEN %s ELSE display_name END,
                    target_lang = CASE WHEN %s <> '' THEN %s ELSE target_lang END,
                    level = CASE WHEN %s <> '' THEN %s ELSE level END,
                    native_lang = CASE WHEN %s <> '' THEN %s ELSE native_lang END,
                    source_system = CASE WHEN %s <> '' THEN %s ELSE source_system END,
                    external_user_id = COALESCE(%s, external_user_id),
                    external_email = CASE WHEN %s <> '' THEN %s ELSE external_email END,
                    external_phone = CASE WHEN %s <> '' THEN %s ELSE external_phone END,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    channel,
                    display_name,
                    display_name,
                    target_lang,
                    target_lang,
                    level,
                    level,
                    native_lang,
                    native_lang,
                    source_system,
                    source_system,
                    external_user_id,
                    external_email,
                    external_email,
                    external_phone,
                    external_phone,
                    row["id"],
                ),
            )
            updated = conn.execute(
                f"SELECT * FROM {LEARNERS_TABLE} WHERE id = %s",
                (row["id"],),
            ).fetchone()
            return dict(updated or row)

        inserted = conn.execute(
            f"""
            INSERT INTO {LEARNERS_TABLE} (
                learner_key,
                channel,
                display_name,
                native_lang,
                target_lang,
                level,
                source_system,
                external_user_id,
                external_email,
                external_phone
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                learner_key,
                channel,
                display_name,
                native_lang,
                target_lang,
                level,
                source_system,
                external_user_id,
                external_email,
                external_phone,
            ),
        ).fetchone()
        return dict(inserted or {})

    def _refresh_learner_metrics(self, conn, learner_id: int) -> None:
        progress = conn.execute(
            f"""
            SELECT
                COUNT(*) AS sessions,
                COALESCE(SUM(duration_min), 0) AS minutes,
                COALESCE(AVG(difficulty), 0) AS avg_difficulty
            FROM {PROGRESS_TABLE}
            WHERE learner_id = %s
            """,
            (learner_id,),
        ).fetchone() or {}
        pronunciation = conn.execute(
            f"""
            SELECT
                COUNT(*) AS samples,
                COALESCE(AVG(score), 0) AS avg_score
            FROM {EVENTS_TABLE}
            WHERE learner_id = %s
              AND event_type = 'pronunciation_attempt'
              AND score IS NOT NULL
            """,
            (learner_id,),
        ).fetchone() or {}
        due = conn.execute(
            f"""
            SELECT COUNT(*) AS due_count
            FROM {REVIEW_TABLE}
            WHERE learner_id = %s
              AND COALESCE(next_due_at, NOW()) <= NOW()
            """,
            (learner_id,),
        ).fetchone() or {}

        conn.execute(
            f"""
            UPDATE {LEARNERS_TABLE}
            SET total_sessions = %s,
                total_minutes = %s,
                avg_difficulty = %s,
                pronunciation_avg_score = %s,
                pronunciation_samples = %s,
                review_due_count = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                int(progress.get("sessions") or 0),
                int(progress.get("minutes") or 0),
                round(float(progress.get("avg_difficulty") or 0), 2),
                round(float(pronunciation.get("avg_score") or 0), 2),
                int(pronunciation.get("samples") or 0),
                int(due.get("due_count") or 0),
                learner_id,
            ),
        )

    def _touch_activity(self, conn, learner_id: int) -> None:
        conn.execute(
            f"UPDATE {LEARNERS_TABLE} SET last_activity_at = NOW(), updated_at = NOW() WHERE id = %s",
            (learner_id,),
        )

    def _upsert_review_item(
        self,
        conn,
        *,
        learner_id: int,
        item_type: str,
        item_key: str,
        source_text: str,
        target_lang: str,
        translation: str = "",
        context_text: str = "",
        skill_area: str = "general",
        notes: str = "",
        score: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        source = _clean_text(source_text, max_chars=260)
        if not source:
            return None

        normalized_type = _clean_text(item_type, max_chars=32) or "item"
        normalized_key = _item_key(item_key or source, fallback_prefix=normalized_type)
        normalized_lang = _normalize_lang(target_lang, default="en")
        translation = _clean_text(translation, max_chars=260)
        context_text = _clean_text(context_text, max_chars=500)
        skill_area = _clean_text(skill_area, max_chars=40) or "general"
        notes = _clean_text(notes, max_chars=320)
        score_value = _round_score(score)
        ratio = _score_ratio(score)
        metadata_json = _json_dumps(metadata or {})

        existing = conn.execute(
            f"""
            SELECT * FROM {REVIEW_TABLE}
            WHERE learner_id = %s
              AND item_type = %s
              AND item_key = %s
              AND target_lang = %s
            """,
            (learner_id, normalized_type, normalized_key, normalized_lang),
        ).fetchone()

        now = _utcnow()
        if existing:
            seen_count = int(existing.get("seen_count") or 0) + 1
            success_count = int(existing.get("success_count") or 0)
            if score_value is None or score_value >= 70:
                success_count += 1
            mastery = round(
                (float(existing.get("mastery_score") or 0.25) * 0.6) + (ratio * 0.4),
                2,
            )
        else:
            seen_count = 1
            success_count = 1 if score_value is None or score_value >= 70 else 0
            mastery = round(max(0.25, ratio * 0.9), 2)

        if score_value is not None and score_value < 55:
            interval_days = 0
            next_due_at = now + timedelta(hours=12)
        elif mastery >= 0.9:
            interval_days = max(7, success_count * 4)
            next_due_at = now + timedelta(days=interval_days)
        elif mastery >= 0.78:
            interval_days = max(4, success_count * 2)
            next_due_at = now + timedelta(days=interval_days)
        elif mastery >= 0.65:
            interval_days = 2
            next_due_at = now + timedelta(days=2)
        else:
            interval_days = 1
            next_due_at = now + timedelta(days=1)

        if existing:
            updated = conn.execute(
                f"""
                UPDATE {REVIEW_TABLE}
                SET source_text = %s,
                    translation = CASE WHEN %s <> '' THEN %s ELSE translation END,
                    context_text = CASE WHEN %s <> '' THEN %s ELSE context_text END,
                    skill_area = %s,
                    notes = CASE WHEN %s <> '' THEN %s ELSE notes END,
                    mastery_score = %s,
                    interval_days = %s,
                    next_due_at = %s,
                    last_seen_at = NOW(),
                    last_result_score = %s,
                    seen_count = %s,
                    success_count = %s,
                    metadata = CASE WHEN %s::jsonb = '{{}}'::jsonb THEN metadata ELSE %s::jsonb END,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (
                    source,
                    translation,
                    translation,
                    context_text,
                    context_text,
                    skill_area,
                    notes,
                    notes,
                    mastery,
                    interval_days,
                    next_due_at,
                    score_value or float(existing.get("last_result_score") or 0),
                    seen_count,
                    success_count,
                    metadata_json,
                    metadata_json,
                    existing["id"],
                ),
            ).fetchone()
            return dict(updated or existing)

        inserted = conn.execute(
            f"""
            INSERT INTO {REVIEW_TABLE} (
                learner_id,
                item_type,
                item_key,
                source_text,
                target_lang,
                translation,
                context_text,
                skill_area,
                notes,
                mastery_score,
                interval_days,
                next_due_at,
                last_seen_at,
                last_result_score,
                seen_count,
                success_count,
                metadata
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s::jsonb
            )
            RETURNING *
            """,
            (
                learner_id,
                normalized_type,
                normalized_key,
                source,
                normalized_lang,
                translation,
                context_text,
                skill_area,
                notes,
                mastery,
                interval_days,
                next_due_at,
                score_value or 0,
                seen_count,
                success_count,
                metadata_json,
            ),
        ).fetchone()
        return dict(inserted or {})

    def record_event(
        self,
        *,
        learner: LearnerContext,
        event_type: str,
        skill_area: str = "general",
        score: Any = None,
        difficulty: Any = None,
        duration_sec: Any = None,
        content_ref: str = "",
        content_text: str = "",
        payload: dict[str, Any] | None = None,
    ) -> bool:
        if not self.ensure_schema():
            return False
        try:
            with self._connect() as conn:
                learner_row = self._ensure_learner(conn, learner)
                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        score,
                        difficulty,
                        duration_sec,
                        content_ref,
                        content_text,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        learner_row["id"],
                        _clean_text(event_type, max_chars=40) or "event",
                        _clean_text(learner.channel, max_chars=24) or "web",
                        _normalize_lang(learner.target_lang, default="en"),
                        _clean_text(skill_area, max_chars=40) or "general",
                        _round_score(score),
                        int(difficulty) if difficulty not in (None, "") else None,
                        int(duration_sec) if duration_sec not in (None, "") else None,
                        _clean_text(content_ref, max_chars=120),
                        _clean_text(content_text, max_chars=1200),
                        _json_dumps(payload or {}),
                    ),
                )
                self._touch_activity(conn, int(learner_row["id"]))
                self._refresh_learner_metrics(conn, int(learner_row["id"]))
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore record_event failed: %s", exc)
            return False

    def save_progress_entry(self, learner: LearnerContext, entry: dict[str, Any]) -> dict[str, Any] | None:
        if not self.ensure_schema():
            return None
        try:
            entry_date_raw = _clean_text(entry.get("date"), max_chars=20)
            try:
                entry_date = date.fromisoformat(entry_date_raw) if entry_date_raw else _utcnow().date()
            except ValueError:
                entry_date = _utcnow().date()

            material = _clean_text(entry.get("material"), max_chars=320)
            duration_min = max(0, min(720, int(float(entry.get("duration_min") or 0))))
            repetitions = max(0, min(300, int(float(entry.get("repetitions") or 0))))
            difficulty = max(1, min(5, int(float(entry.get("difficulty") or 3))))
            notes = _clean_text(entry.get("notes"), max_chars=1000)

            with self._connect() as conn:
                learner_row = self._ensure_learner(conn, learner)
                inserted = conn.execute(
                    f"""
                    INSERT INTO {PROGRESS_TABLE} (
                        learner_id,
                        entry_date,
                        material,
                        duration_min,
                        repetitions,
                        difficulty,
                        notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        learner_row["id"],
                        entry_date,
                        material,
                        duration_min,
                        repetitions,
                        difficulty,
                        notes,
                    ),
                ).fetchone()

                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        difficulty,
                        duration_sec,
                        content_ref,
                        content_text,
                        payload
                    )
                    VALUES (%s, 'manual_progress', %s, %s, 'practice', %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        learner_row["id"],
                        learner.channel,
                        learner.target_lang,
                        difficulty,
                        duration_min * 60,
                        material[:120],
                        notes[:320],
                        _json_dumps(
                            {
                                "repetitions": repetitions,
                                "entry_date": entry_date.isoformat(),
                            }
                        ),
                    ),
                )

                self._touch_activity(conn, int(learner_row["id"]))
                self._refresh_learner_metrics(conn, int(learner_row["id"]))
                self.last_error = ""
                return self._serialize_progress_row(dict(inserted or {}))
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore save_progress_entry failed: %s", exc)
            return None

    def get_progress_entries(self, learner: LearnerContext | str, *, limit: int = 500) -> list[dict[str, Any]]:
        if not self.ensure_schema():
            return []
        try:
            with self._connect() as conn:
                learner_row = self._find_learner_row(conn, learner)
                if not learner_row:
                    return []
                rows = conn.execute(
                    f"""
                    SELECT *
                    FROM {PROGRESS_TABLE}
                    WHERE learner_id = %s
                    ORDER BY entry_date ASC, id ASC
                    LIMIT %s
                    """,
                    (learner_row["id"], max(1, min(5000, int(limit)))),
                ).fetchall()
                self.last_error = ""
                return [self._serialize_progress_row(dict(row)) for row in rows]
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore get_progress_entries failed: %s", exc)
            return []

    def delete_progress_entry(self, learner: LearnerContext | str, entry_id: int) -> bool:
        if not self.ensure_schema():
            return False
        try:
            with self._connect() as conn:
                learner_row = self._find_learner_row(conn, learner)
                if not learner_row:
                    return False
                conn.execute(
                    f"DELETE FROM {PROGRESS_TABLE} WHERE id = %s AND learner_id = %s",
                    (int(entry_id), learner_row["id"]),
                )
                self._refresh_learner_metrics(conn, int(learner_row["id"]))
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore delete_progress_entry failed: %s", exc)
            return False

    def record_practice_analysis(
        self,
        learner: LearnerContext,
        *,
        text: str,
        analysis: dict[str, Any],
    ) -> bool:
        if not self.ensure_schema():
            return False
        try:
            with self._connect() as conn:
                learner_row = self._ensure_learner(conn, learner)
                learner_id = int(learner_row["id"])
                difficulty = analysis.get("difficulty_score")
                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        difficulty,
                        content_text,
                        payload
                    )
                    VALUES (%s, 'practice_analysis', %s, %s, 'analysis', %s, %s, %s::jsonb)
                    """,
                    (
                        learner_id,
                        learner.channel,
                        learner.target_lang,
                        int(difficulty) if difficulty not in (None, "") else None,
                        _clean_text(text, max_chars=1200),
                        _json_dumps(analysis),
                    ),
                )

                for item in (analysis.get("pronunciation_tips") or [])[:6]:
                    if not isinstance(item, dict):
                        continue
                    word = _clean_text(item.get("word"), max_chars=120)
                    tip = _clean_text(item.get("tip"), max_chars=260)
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="pronunciation_word",
                        item_key=word,
                        source_text=word,
                        target_lang=learner.target_lang,
                        skill_area="pronunciation",
                        notes=tip,
                        metadata={"phonetic": _clean_text(item.get("phonetic"), max_chars=120)},
                    )

                for item in (analysis.get("key_vocabulary") or [])[:8]:
                    if not isinstance(item, dict):
                        continue
                    word = _clean_text(item.get("word"), max_chars=120)
                    meaning = _clean_text(item.get("meaning"), max_chars=160)
                    example = _clean_text(item.get("example"), max_chars=260)
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="vocabulary_word",
                        item_key=word,
                        source_text=word,
                        target_lang=learner.target_lang,
                        translation=meaning,
                        context_text=example,
                        skill_area="vocabulary",
                        notes="Vocabulário destacado na análise da sessão.",
                    )

                for phrase in (analysis.get("shadowing_focus") or [])[:4]:
                    clean_phrase = _clean_text(phrase, max_chars=220)
                    if len(clean_phrase.split()) < 2:
                        continue
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="shadow_phrase",
                        item_key=clean_phrase,
                        source_text=clean_phrase,
                        target_lang=learner.target_lang,
                        skill_area="shadowing",
                        notes="Ponto de foco recomendado para shadowing.",
                    )

                self._touch_activity(conn, learner_id)
                self._refresh_learner_metrics(conn, learner_id)
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore record_practice_analysis failed: %s", exc)
            return False

    def record_practice_generation(
        self,
        learner: LearnerContext,
        *,
        topic: str,
        text_type: str,
        text_length: str,
        focus: str,
        generated_text: str,
    ) -> bool:
        return self.record_event(
            learner=learner,
            event_type="practice_material_generated",
            skill_area="practice",
            content_ref=f"{_clean_text(text_type, max_chars=40)}:{_clean_text(text_length, max_chars=20)}",
            content_text=generated_text,
            payload={
                "topic": _clean_text(topic, max_chars=160),
                "focus": _clean_text(focus, max_chars=220),
            },
        )

    def record_conversation_turn(
        self,
        learner: LearnerContext,
        *,
        user_text: str,
        ai_text: str,
        history_size: int = 0,
    ) -> bool:
        return self.record_event(
            learner=learner,
            event_type="conversation_turn",
            skill_area="conversation",
            content_text=user_text,
            payload={
                "ai_text": _clean_text(ai_text, max_chars=320),
                "history_size": max(0, int(history_size or 0)),
                "token_variety": len(_extract_phrase_tokens(user_text, limit=30)),
            },
        )

    def record_conversation_lesson(
        self,
        learner: LearnerContext,
        *,
        lesson_payload: dict[str, Any],
    ) -> bool:
        if not self.ensure_schema():
            return False
        try:
            with self._connect() as conn:
                learner_row = self._ensure_learner(conn, learner)
                learner_id = int(learner_row["id"])
                pronunciation = lesson_payload.get("pronunciation_feedback") or {}
                pronunciation_score = _round_score(pronunciation.get("score"))
                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        score,
                        content_text,
                        payload
                    )
                    VALUES (%s, 'conversation_lesson', %s, %s, 'conversation_coach', %s, %s, %s::jsonb)
                    """,
                    (
                        learner_id,
                        learner.channel,
                        learner.target_lang,
                        pronunciation_score,
                        _clean_text((lesson_payload.get("lesson") or {}).get("summary"), max_chars=500),
                        _json_dumps(lesson_payload),
                    ),
                )

                lesson = lesson_payload.get("lesson") or {}
                for item in (lesson.get("vocabulary") or [])[:6]:
                    if not isinstance(item, dict):
                        continue
                    word = _clean_text(item.get("word"), max_chars=120)
                    meaning = _clean_text(item.get("meaning"), max_chars=160)
                    example = _clean_text(item.get("example"), max_chars=260)
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="conversation_vocab",
                        item_key=word,
                        source_text=word,
                        target_lang=learner.target_lang,
                        translation=meaning,
                        context_text=example,
                        skill_area="vocabulary",
                        notes="Vocabulário relevante da conversa.",
                    )

                for item in (lesson.get("corrections") or [])[:6]:
                    if not isinstance(item, dict):
                        continue
                    corrected = _clean_text(item.get("corrected"), max_chars=220)
                    original = _clean_text(item.get("original"), max_chars=220)
                    tip = _clean_text(item.get("tip"), max_chars=260)
                    if not corrected:
                        continue
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="correction_phrase",
                        item_key=corrected,
                        source_text=corrected,
                        target_lang=learner.target_lang,
                        context_text=original,
                        skill_area="grammar",
                        notes=tip or "Correção gerada a partir da conversa.",
                    )

                for phrase in (pronunciation.get("drill_phrases") or [])[:4]:
                    drill = _clean_text(phrase, max_chars=220)
                    if not drill:
                        continue
                    self._upsert_review_item(
                        conn,
                        learner_id=learner_id,
                        item_type="drill_phrase",
                        item_key=drill,
                        source_text=drill,
                        target_lang=learner.target_lang,
                        skill_area="pronunciation",
                        notes=_clean_text(pronunciation.get("summary"), max_chars=220),
                        score=pronunciation_score,
                    )

                self._touch_activity(conn, learner_id)
                self._refresh_learner_metrics(conn, learner_id)
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore record_conversation_lesson failed: %s", exc)
            return False

    def record_pronunciation_attempt(
        self,
        learner: LearnerContext,
        *,
        expected_phrase: str,
        transcript: str,
        score: Any,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if not self.ensure_schema():
            return False
        try:
            with self._connect() as conn:
                learner_row = self._ensure_learner(conn, learner)
                learner_id = int(learner_row["id"])
                rounded_score = _round_score(score)
                payload = metadata or {}
                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        score,
                        content_text,
                        payload
                    )
                    VALUES (%s, 'pronunciation_attempt', %s, %s, 'pronunciation', %s, %s, %s::jsonb)
                    """,
                    (
                        learner_id,
                        learner.channel,
                        learner.target_lang,
                        rounded_score,
                        _clean_text(transcript, max_chars=600),
                        _json_dumps(
                            {
                                "expected_phrase": _clean_text(expected_phrase, max_chars=260),
                                **payload,
                            }
                        ),
                    ),
                )
                self._upsert_review_item(
                    conn,
                    learner_id=learner_id,
                    item_type="pronunciation_phrase",
                    item_key=expected_phrase,
                    source_text=expected_phrase,
                    target_lang=learner.target_lang,
                    context_text=transcript,
                    skill_area="pronunciation",
                    notes=_clean_text((metadata or {}).get("lesson_tip"), max_chars=220),
                    score=rounded_score,
                    metadata=metadata,
                )

                missing_words = (metadata or {}).get("missing_words") or []
                if isinstance(missing_words, list):
                    for word in missing_words[:5]:
                        clean_word = _clean_text(word, max_chars=120)
                        if not clean_word:
                            continue
                        self._upsert_review_item(
                            conn,
                            learner_id=learner_id,
                            item_type="pronunciation_word",
                            item_key=clean_word,
                            source_text=clean_word,
                            target_lang=learner.target_lang,
                            skill_area="pronunciation",
                            notes="Palavra ausente em uma tentativa de pronúncia recente.",
                            score=max(10.0, min(60.0, (rounded_score or 40.0) - 20.0)),
                        )

                self._touch_activity(conn, learner_id)
                self._refresh_learner_metrics(conn, learner_id)
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore record_pronunciation_attempt failed: %s", exc)
            return False

    def get_dashboard(self, learner: LearnerContext | str, *, fallback_lang: str = "en") -> dict[str, Any]:
        learner_key = learner.learner_key if isinstance(learner, LearnerContext) else learner
        channel = learner.channel if isinstance(learner, LearnerContext) else "web"
        level = learner.level if isinstance(learner, LearnerContext) else "A1"
        dashboard = {
            "learner": {
                "learner_key": _normalize_key(learner_key),
                "target_lang": _normalize_lang(fallback_lang, default="en"),
                "channel": _clean_text(channel, max_chars=24) or "web",
                "level": _clean_text(level, max_chars=16) or "A1",
            },
            "summary": {
                "sessions": 0,
                "minutes": 0,
                "avg_difficulty": 0.0,
                "pronunciation_avg_score": 0.0,
                "pronunciation_samples": 0,
                "review_due": 0,
                "tracked_items": 0,
                "active_days_7d": 0,
                "last_activity_at": "",
            },
            "review_queue": [],
            "recommendations": [],
            "weak_points": [],
            "strengths": [],
            "flashcard_pool": [],
            "language_breakdown": [],
        }
        if not self.ensure_schema():
            return dashboard
        try:
            with self._connect() as conn:
                learner_row = self._find_learner_row(conn, learner)
                if not learner_row:
                    return dashboard

                learner = dict(learner_row)
                review_due = conn.execute(
                    f"""
                    SELECT *
                    FROM {REVIEW_TABLE}
                    WHERE learner_id = %s
                      AND COALESCE(next_due_at, NOW()) <= NOW()
                    ORDER BY COALESCE(next_due_at, NOW()) ASC, mastery_score ASC, seen_count DESC
                    LIMIT 6
                    """,
                    (learner["id"],),
                ).fetchall()
                weak_points = conn.execute(
                    f"""
                    SELECT *
                    FROM {REVIEW_TABLE}
                    WHERE learner_id = %s
                    ORDER BY mastery_score ASC, seen_count DESC, updated_at DESC
                    LIMIT 5
                    """,
                    (learner["id"],),
                ).fetchall()
                strengths = conn.execute(
                    f"""
                    SELECT *
                    FROM {REVIEW_TABLE}
                    WHERE learner_id = %s
                      AND seen_count >= 2
                    ORDER BY mastery_score DESC, success_count DESC, updated_at DESC
                    LIMIT 5
                    """,
                    (learner["id"],),
                ).fetchall()
                flashcard_pool = conn.execute(
                    f"""
                    WITH ranked_flashcards AS (
                        SELECT
                            *,
                            ROW_NUMBER() OVER (
                                PARTITION BY target_lang
                                ORDER BY
                                    CASE
                                        WHEN COALESCE(next_due_at, NOW()) <= NOW() THEN 0
                                        ELSE 1
                                    END ASC,
                                    mastery_score ASC,
                                    seen_count DESC,
                                    updated_at DESC
                            ) AS lang_rank
                        FROM {REVIEW_TABLE}
                        WHERE learner_id = %s
                    )
                    SELECT *
                    FROM ranked_flashcards
                    WHERE lang_rank <= 8
                    ORDER BY
                        CASE
                            WHEN COALESCE(next_due_at, NOW()) <= NOW() THEN 0
                            ELSE 1
                        END ASC,
                        mastery_score ASC,
                        seen_count DESC,
                        updated_at DESC
                    LIMIT 32
                    """,
                    (learner["id"],),
                ).fetchall()
                tracked = conn.execute(
                    f"SELECT COUNT(*) AS total FROM {REVIEW_TABLE} WHERE learner_id = %s",
                    (learner["id"],),
                ).fetchone() or {}
                language_breakdown = conn.execute(
                    f"""
                    SELECT
                        target_lang,
                        COUNT(*) AS total_items,
                        COUNT(*) FILTER (
                            WHERE COALESCE(next_due_at, NOW()) <= NOW()
                        ) AS due_items,
                        AVG(mastery_score) AS avg_mastery
                    FROM {REVIEW_TABLE}
                    WHERE learner_id = %s
                    GROUP BY target_lang
                    ORDER BY COUNT(*) DESC, target_lang ASC
                    """,
                    (learner["id"],),
                ).fetchall()
                active_days = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT DATE(created_at)) AS active_days
                    FROM {EVENTS_TABLE}
                    WHERE learner_id = %s
                      AND created_at >= NOW() - INTERVAL '7 days'
                    """,
                    (learner["id"],),
                ).fetchone() or {}

                dashboard["learner"] = {
                    "learner_key": learner["learner_key"],
                    "target_lang": learner["target_lang"],
                    "channel": learner["channel"],
                    "level": learner["level"],
                    "display_name": learner.get("display_name") or "",
                    "source_system": learner.get("source_system") or "shadowing_practice",
                    "external_user_id": int(learner["external_user_id"]) if learner.get("external_user_id") else None,
                    "external_email": learner.get("external_email") or "",
                    "external_phone": learner.get("external_phone") or "",
                }
                dashboard["summary"] = {
                    "sessions": int(learner.get("total_sessions") or 0),
                    "minutes": int(learner.get("total_minutes") or 0),
                    "avg_difficulty": round(float(learner.get("avg_difficulty") or 0), 2),
                    "pronunciation_avg_score": round(float(learner.get("pronunciation_avg_score") or 0), 1),
                    "pronunciation_samples": int(learner.get("pronunciation_samples") or 0),
                    "review_due": int(learner.get("review_due_count") or 0),
                    "tracked_items": int(tracked.get("total") or 0),
                    "active_days_7d": int(active_days.get("active_days") or 0),
                    "last_activity_at": _serialize_datetime(learner.get("last_activity_at")),
                }
                dashboard["review_queue"] = [
                    self._serialize_review_item(dict(item))
                    for item in review_due
                ]
                dashboard["weak_points"] = [
                    self._serialize_review_item(dict(item))
                    for item in weak_points
                ]
                dashboard["strengths"] = [
                    self._serialize_review_item(dict(item))
                    for item in strengths
                ]
                dashboard["flashcard_pool"] = [
                    self._serialize_review_item(dict(item))
                    for item in flashcard_pool
                ]
                dashboard["language_breakdown"] = [
                    {
                        "target_lang": _normalize_lang(item.get("target_lang"), default="en"),
                        "total_items": int(item.get("total_items") or 0),
                        "due_items": int(item.get("due_items") or 0),
                        "avg_mastery": round(float(item.get("avg_mastery") or 0), 2),
                    }
                    for item in language_breakdown
                ]
                dashboard["recommendations"] = self._build_recommendations(
                    dashboard["review_queue"],
                    dashboard["weak_points"],
                    dashboard["strengths"],
                    target_lang=learner["target_lang"],
                )
                self.last_error = ""
                return dashboard
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore get_dashboard failed: %s", exc)
            return dashboard

    def review_item(
        self,
        learner: LearnerContext | str,
        *,
        item_id: int,
        score: Any,
        notes: str = "",
    ) -> dict[str, Any] | None:
        if not self.ensure_schema():
            return None
        try:
            with self._connect() as conn:
                learner_row = self._find_learner_row(conn, learner)
                if not learner_row:
                    self.last_error = "Learner não encontrado para revisão."
                    return None

                row = conn.execute(
                    f"""
                    SELECT *
                    FROM {REVIEW_TABLE}
                    WHERE id = %s
                      AND learner_id = %s
                    """,
                    (int(item_id), int(learner_row["id"])),
                ).fetchone()
                if not row:
                    self.last_error = "Item de revisão não encontrado."
                    return None

                current = dict(row)
                merged_notes = _clean_text(notes, max_chars=320) or _clean_text(
                    current.get("notes"),
                    max_chars=320,
                )
                metadata = current.get("metadata")
                if not isinstance(metadata, dict):
                    metadata = {}

                updated = self._upsert_review_item(
                    conn,
                    learner_id=int(learner_row["id"]),
                    item_type=current.get("item_type") or "item",
                    item_key=current.get("item_key") or current.get("source_text") or "",
                    source_text=current.get("source_text") or "",
                    target_lang=current.get("target_lang") or (
                        learner.target_lang if isinstance(learner, LearnerContext) else "en"
                    ),
                    translation=current.get("translation") or "",
                    context_text=current.get("context_text") or "",
                    skill_area=current.get("skill_area") or "general",
                    notes=merged_notes,
                    score=score,
                    metadata=metadata,
                )
                if not updated:
                    self.last_error = "Falha ao atualizar o item de revisão."
                    return None

                rounded_score = _round_score(score)
                channel = learner.channel if isinstance(learner, LearnerContext) else "web"
                target_lang = (
                    learner.target_lang if isinstance(learner, LearnerContext)
                    else (current.get("target_lang") or "en")
                )
                conn.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (
                        learner_id,
                        event_type,
                        channel,
                        target_lang,
                        skill_area,
                        score,
                        content_ref,
                        content_text,
                        payload
                    )
                    VALUES (%s, 'review_feedback', %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        int(learner_row["id"]),
                        _clean_text(channel, max_chars=24) or "web",
                        _normalize_lang(target_lang, default="en"),
                        _clean_text(current.get("skill_area"), max_chars=40) or "general",
                        rounded_score,
                        f"{_clean_text(current.get('item_type'), max_chars=32) or 'item'}:{int(item_id)}",
                        _clean_text(current.get("source_text"), max_chars=260),
                        _json_dumps(
                            {
                                "review_item_id": int(item_id),
                                "score": rounded_score,
                                "notes": merged_notes,
                            }
                        ),
                    ),
                )

                self._touch_activity(conn, int(learner_row["id"]))
                self._refresh_learner_metrics(conn, int(learner_row["id"]))
            self.last_error = ""
            return self._serialize_review_item(updated)
        except Exception as exc:
            self.last_error = str(exc)
            logger.warning("AdaptiveLearningStore review_item failed: %s", exc)
            return None

    @staticmethod
    def _serialize_progress_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": int(row.get("id") or 0),
            "date": _serialize_datetime(row.get("entry_date")),
            "material": row.get("material") or "",
            "duration_min": int(row.get("duration_min") or 0),
            "repetitions": int(row.get("repetitions") or 0),
            "difficulty": int(row.get("difficulty") or 0),
            "notes": row.get("notes") or "",
        }

    @staticmethod
    def _serialize_review_item(row: dict[str, Any]) -> dict[str, Any]:
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        return {
            "id": int(row.get("id") or 0),
            "item_type": row.get("item_type") or "",
            "source_text": row.get("source_text") or "",
            "translation": row.get("translation") or "",
            "context_text": row.get("context_text") or "",
            "skill_area": row.get("skill_area") or "",
            "notes": row.get("notes") or "",
            "mastery_score": round(float(row.get("mastery_score") or 0), 2),
            "interval_days": int(row.get("interval_days") or 0),
            "last_result_score": round(float(row.get("last_result_score") or 0), 1),
            "seen_count": int(row.get("seen_count") or 0),
            "success_count": int(row.get("success_count") or 0),
            "next_due_at": _serialize_datetime(row.get("next_due_at")),
            "updated_at": _serialize_datetime(row.get("updated_at")),
            "target_lang": row.get("target_lang") or "",
            "metadata": metadata,
        }

    def _build_recommendations(
        self,
        review_queue: list[dict[str, Any]],
        weak_points: list[dict[str, Any]],
        strengths: list[dict[str, Any]],
        *,
        target_lang: str,
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []

        for item in review_queue[:3]:
            recommendations.append(
                {
                    "kind": "review_due",
                    "title": f"Revise: {item.get('source_text', '')}",
                    "reason": "Este item já venceu na repetição espaçada e deve ser revisado hoje.",
                    "target_lang": target_lang,
                    "skill_area": item.get("skill_area") or "general",
                    "payload": {
                        "text": item.get("source_text") or "",
                        "translation": item.get("translation") or "",
                        "lang": target_lang,
                    },
                }
            )

        weakest = weak_points[0] if weak_points else None
        if weakest:
            area = weakest.get("skill_area") or "general"
            if area == "pronunciation":
                recommendations.append(
                    {
                        "kind": "pronunciation_drill",
                        "title": "Faça um drill de pronúncia curto",
                        "reason": f"Sua menor maestria atual está em pronúncia: “{weakest.get('source_text', '')}”.",
                        "target_lang": target_lang,
                        "skill_area": area,
                        "payload": {
                            "text": weakest.get("source_text") or "",
                            "lang": target_lang,
                            "mode": "shadowing",
                        },
                    }
                )
            elif area == "grammar":
                recommendations.append(
                    {
                        "kind": "conversation_coach",
                        "title": "Gere uma aula de conversa focada em correções",
                        "reason": "Suas últimas correções ainda têm baixa retenção.",
                        "target_lang": target_lang,
                        "skill_area": area,
                        "payload": {
                            "lesson_focus": "corrections",
                            "lang": target_lang,
                        },
                    }
                )
            else:
                focus_words = ", ".join(
                    item.get("source_text") or ""
                    for item in weak_points[:3]
                    if item.get("skill_area") == "vocabulary"
                ).strip(", ")
                recommendations.append(
                    {
                        "kind": "targeted_practice",
                        "title": "Gere um texto curto com foco no seu vocabulário fraco",
                        "reason": (
                            f"Vale reciclar palavras como {focus_words}."
                            if focus_words else
                            "Vale reforçar seu vocabulário ativo antes de avançar."
                        ),
                        "target_lang": target_lang,
                        "skill_area": area,
                        "payload": {
                            "target_lang": target_lang,
                            "text_length": "short",
                            "text_type": "dialogue",
                        },
                    }
                )

        if strengths:
            strongest = strengths[0]
            recommendations.append(
                {
                    "kind": "stretch_goal",
                    "title": "Suba um pouco a dificuldade",
                    "reason": f"Você está indo bem em “{strongest.get('source_text', '')}”; é um bom momento para alongar o treino.",
                    "target_lang": target_lang,
                    "skill_area": strongest.get("skill_area") or "general",
                    "payload": {
                        "target_lang": target_lang,
                        "text_length": "medium",
                        "text_type": "casual_chat",
                        "focus": "fluência com frases mais naturais",
                    },
                }
            )

        deduped: list[dict[str, Any]] = []
        seen_titles: set[str] = set()
        for item in recommendations:
            title = _clean_text(item.get("title"), max_chars=120)
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            deduped.append(item)
            if len(deduped) >= 5:
                break
        return deduped
