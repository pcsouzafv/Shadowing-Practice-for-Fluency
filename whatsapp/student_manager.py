"""
Student Manager
================
Gerencia os alunos inscritos no serviço de mini-aulas WhatsApp.
Persiste os dados em JSON (data/whatsapp_students.json).

Idioma fixo: Inglês 🇬🇧 (altere ACTIVE_LANG no .env para mudar no futuro)
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "whatsapp_students.json"

# Idioma ativo — mude ACTIVE_LANG no .env para trocar de idioma
import os as _os

ACTIVE_LANG: str = _os.environ.get("ACTIVE_LANG", "en")

SUPPORTED_LANGS: dict[str, dict[str, str]] = {
    "en": {"name": "Inglês 🇬🇧", "voice": "en_US-amy-medium", "flag": "🇬🇧"},
}

LEVELS = ["A1", "A2", "B1", "B2"]


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class StudentManager:
    """Thread-safe gerenciador de alunos do WhatsApp."""

    def __init__(self, filepath: Path | str = _DEFAULT_FILE) -> None:
        self._path = Path(filepath)
        self._lock = threading.Lock()
        self._students: dict[str, dict[str, Any]] = {}
        self._load()

    # ─────────────────────── Persistence ─────────────────────────────────────

    def _load(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    raw = json.load(f)
                normalized: dict[str, dict[str, Any]] = {}
                if isinstance(raw, list):
                    items = [s for s in raw if isinstance(s, dict)]
                elif isinstance(raw, dict):
                    items = []
                    for phone_key, student in raw.items():
                        if not isinstance(student, dict):
                            continue
                        candidate = dict(student)
                        candidate.setdefault("phone", str(phone_key))
                        items.append(candidate)
                else:
                    items = []

                for student in items:
                    raw_phone = str(student.get("phone", "")).strip()
                    phone = self._normalize_phone_key(raw_phone)
                    if not phone:
                        continue
                    candidate = dict(student)
                    candidate["phone"] = phone
                    candidate.setdefault("voice_responses", True)

                    existing = normalized.get(phone)
                    if not existing:
                        normalized[phone] = candidate
                        continue

                    # Keep the most recently updated record when duplicates exist.
                    if str(candidate.get("updated_at", "")) >= str(existing.get("updated_at", "")):
                        normalized[phone] = candidate

                self._students = normalized
            except Exception as exc:
                logger.warning("Could not load students file: %s", exc)
                self._students = {}
        else:
            self._students = {}
            self._save_locked()

    @staticmethod
    def _normalize_phone_key(phone: str) -> str:
        raw = str(phone or "").strip()
        if not raw:
            return ""
        raw_lc = raw.lower()
        if raw_lc.endswith("@s.whatsapp.net") or raw_lc.endswith("@c.us"):
            local = raw.split("@", 1)[0]
            digits = "".join(ch for ch in local if ch.isdigit())
            return digits or local
        return raw

    def _save_locked(self) -> None:
        """Must be called within self._lock."""
        try:
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._students, f, ensure_ascii=False, indent=2)
            tmp.replace(self._path)
        except Exception as exc:
            logger.error("Could not save students file: %s", exc)

    def save(self) -> None:
        with self._lock:
            self._save_locked()

    # ─────────────────────── Student CRUD ────────────────────────────────────

    def get(self, phone: str) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._students.get(phone, {})) or None

    def exists(self, phone: str) -> bool:
        return phone in self._students

    def register(
        self,
        phone: str,
        *,
        name: str = "",
        lang: str = "en",
        level: str = "A1",
    ) -> dict[str, Any]:
        """Cria ou re-ativa um aluno."""
        lang = lang if lang in SUPPORTED_LANGS else "en"
        level = level if level in LEVELS else "A1"
        with self._lock:
            existing = self._students.get(phone)
            if existing:
                existing["active"] = True
                existing.setdefault("voice_responses", True)
                existing["updated_at"] = _now_iso()
                self._save_locked()
                return dict(existing)

            student = {
                "phone": phone,
                "name": name or phone,
                "lang": lang,
                "level": level,
                "lesson_index": 0,
                "active": True,
                "streak": 0,
                "last_lesson_date": "",
                "last_seen": _now_iso(),
                "registered_at": _now_iso(),
                "updated_at": _now_iso(),
                "pending_lang_choice": False,
                "pending_level_choice": False,
                "voice_responses": True,
                "total_lessons_sent": 0,
                "total_replies": 0,
            }
            self._students[phone] = student
            self._save_locked()
            return dict(student)

    def update(self, phone: str, **kwargs: Any) -> bool:
        with self._lock:
            student = self._students.get(phone)
            if not student:
                return False
            for k, v in kwargs.items():
                student[k] = v
            student["updated_at"] = _now_iso()
            self._save_locked()
            return True

    def deactivate(self, phone: str) -> bool:
        return self.update(phone, active=False)

    def advance_lesson(self, phone: str, max_index: int) -> int:
        """Avança o índice de lição e atualiza streak. Retorna o novo índice."""
        with self._lock:
            student = self._students.get(phone)
            if not student:
                return 0
            today = date.today().isoformat()
            last = student.get("last_lesson_date", "")
            if last == today:
                return int(student.get("lesson_index", 0))

            new_index = (int(student.get("lesson_index", 0)) + 1) % max(1, max_index)
            # Streak logic
            from datetime import timedelta
            try:
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                streak = int(student.get("streak", 0))
                student["streak"] = streak + 1 if last == yesterday else 1
            except Exception:
                student["streak"] = 1

            student["lesson_index"] = new_index
            student["last_lesson_date"] = today
            student["total_lessons_sent"] = int(student.get("total_lessons_sent", 0)) + 1
            student["updated_at"] = _now_iso()
            self._save_locked()
            return new_index

    def record_reply(self, phone: str) -> None:
        with self._lock:
            student = self._students.get(phone)
            if student:
                student["total_replies"] = int(student.get("total_replies", 0)) + 1
                student["last_seen"] = _now_iso()
                student["updated_at"] = _now_iso()
                self._save_locked()

    def all_active(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(s) for s in self._students.values() if s.get("active")]

    def all_students(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(s) for s in self._students.values()]

    def count(self) -> dict[str, int]:
        with self._lock:
            total = len(self._students)
            active = sum(1 for s in self._students.values() if s.get("active"))
            return {"total": total, "active": active, "inactive": total - active}
