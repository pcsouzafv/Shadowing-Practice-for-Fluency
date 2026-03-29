"""
WhatsApp Lesson Scheduler
==========================
Agendador de mini-aulas baseado em APScheduler.
Envia lições automáticas para todos os alunos ativos nos horários configurados.

Horários padrão: 9h e 19h (horário de Brasília, UTC-3)
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    _APSCHEDULER_AVAILABLE = True
except ModuleNotFoundError:
    BackgroundScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]
    _APSCHEDULER_AVAILABLE = False

if TYPE_CHECKING:
    from .evolution_client import EvolutionClient
    from .student_manager import StudentManager
    from .lesson_curriculum import LessonCurriculum

logger = logging.getLogger(__name__)


class LessonScheduler:
    """Agendador de mini-aulas para WhatsApp.

    Inicia com o Flask app e roda em background thread via APScheduler.
    """

    def __init__(
        self,
        client: "EvolutionClient",
        students: "StudentManager",
        curriculum: "LessonCurriculum",
        models_dir: Path | None = None,
    ) -> None:
        self.client = client
        self.students = students
        self.curriculum = curriculum
        self.models_dir = models_dir or Path(__file__).resolve().parent.parent / "models"
        self._scheduler = (
            BackgroundScheduler(timezone="America/Sao_Paulo")
            if _APSCHEDULER_AVAILABLE
            else None
        )
        self._running = False

    def start(self, morning_hour: int = 9, evening_hour: int = 19) -> None:
        """Inicia o agendador com dois envios por dia."""
        if not _APSCHEDULER_AVAILABLE or self._scheduler is None:
            logger.warning(
                "APScheduler is not installed. Automatic lessons are disabled; manual send still works."
            )
            self._running = False
            return
        if self._running:
            logger.warning("Scheduler already running.")
            return

        # Envio matinal
        self._scheduler.add_job(
            func=self._send_daily_lesson,
            trigger=CronTrigger(hour=morning_hour, minute=0, timezone="America/Sao_Paulo"),
            id="morning_lesson",
            name="Mini Aula Matinal",
            replace_existing=True,
            misfire_grace_time=300,
        )

        # Envio vespertino
        self._scheduler.add_job(
            func=self._send_daily_lesson,
            trigger=CronTrigger(hour=evening_hour, minute=0, timezone="America/Sao_Paulo"),
            id="evening_lesson",
            name="Mini Aula Vespertina",
            replace_existing=True,
            misfire_grace_time=300,
        )

        self._scheduler.start()
        self._running = True
        logger.info(
            "LessonScheduler started — lessons at %02dh00 and %02dh00 (America/Sao_Paulo)",
            morning_hour,
            evening_hour,
        )

    def stop(self) -> None:
        if self._running and self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("LessonScheduler stopped.")

    def send_now(self, phone: str) -> dict:
        """Envia uma lição imediatamente para um aluno específico (usado no webhook)."""
        student = self.students.get(phone)
        if not student:
            return {"ok": False, "error": "Student not found"}
        return self._deliver_lesson(student)

    # ─────────────────────────── Internal ────────────────────────────────────

    def _send_daily_lesson(self) -> None:
        """Job: envia lição para todos os alunos ativos."""
        active = self.students.all_active()
        logger.info("Sending daily lesson to %d active students.", len(active))
        for student in active:
            try:
                phone = str(student.get("phone", "")).strip()
                phone_lc = phone.lower()
                if phone_lc.endswith("@lid") or phone_lc.endswith("@g.us"):
                    logger.warning("Skipping unsupported WhatsApp ID for delivery: %s", phone)
                    continue
                result = self._deliver_lesson(student)
                if result.get("ok"):
                    new_idx = self.students.advance_lesson(
                        student["phone"],
                        max_index=self.curriculum.total(student.get("lang", "en")),
                    )
                    logger.debug(
                        "Lesson sent to %s | next lesson index: %d",
                        student["phone"][-4:],
                        new_idx,
                    )
                else:
                    logger.warning("Failed to deliver lesson to %s: %s", student["phone"][-4:], result)
            except Exception as exc:
                logger.error("Error delivering lesson to %s: %s", student.get("phone", "?")[-4:], exc)

    def _deliver_lesson(self, student: dict) -> dict:
        """Envia texto + áudio da lição para um aluno."""
        phone = student["phone"]
        lang = student.get("lang", "en")
        index = int(student.get("lesson_index", 0))
        streak = int(student.get("streak", 0))

        lesson = self.curriculum.get(lang, index)
        if not lesson:
            return {"ok": False, "error": f"No lesson found for lang={lang} index={index}"}

        # 1 — Enviar mensagem de texto
        message = self.curriculum.format_lesson_message(lesson, streak=streak)
        text_result = self.client.send_text(phone, message)

        if "error" in text_result:
            return {"ok": False, "error": text_result["error"]}

        # 2 — Gerar e enviar áudio TTS (Piper)
        try:
            audio_b64 = self._generate_audio(lesson.phrase, lang)
            if audio_b64:
                self.client.send_audio_b64(phone, audio_b64, ptt=True)
                # Enviar também o exemplo completo
                example_b64 = self._generate_audio(lesson.example, lang)
                if example_b64:
                    self.client.send_audio_b64(phone, example_b64, ptt=True)
        except Exception as exc:
            logger.warning("TTS audio generation failed for %s: %s", phone[-4:], exc)

        return {"ok": True, "lesson_id": lesson.id, "phone": phone}

    def _generate_audio(self, text: str, lang: str) -> str | None:
        """Gera áudio OGG/base64 com Piper TTS."""
        from .evolution_client import EvolutionClient

        voice_map = {
            "en": "en_US-amy-medium",
            "es": "es_ES-sharvard-medium",
            "fr": "fr_FR-siwis-medium",
            "de": "de_DE-thorsten-medium",
            "it": "it_IT-paola-medium",
        }
        voice = voice_map.get(lang, "en_US-amy-medium")
        model_path = self.models_dir / f"{voice}.onnx"

        if not model_path.exists():
            logger.warning("Piper model not found: %s", model_path)
            return None

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_f:
            wav_path = Path(wav_f.name)

        try:
            result = subprocess.run(
                [
                    "piper",
                    "--model", str(model_path),
                    "--output_file", str(wav_path),
                ],
                input=text,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning("Piper TTS error: %s", result.stderr)
                return None

            with open(wav_path, "rb") as f:
                wav_bytes = f.read()

            return EvolutionClient.wav_bytes_to_ogg_b64(wav_bytes)
        except Exception as exc:
            logger.error("Audio generation failed: %s", exc)
            return None
        finally:
            wav_path.unlink(missing_ok=True)
