"""
WhatsApp Message Handler
==========================
Processa mensagens recebidas via webhook da Evolution API e
gera respostas adequadas para o assistente de mini-aulas de inglês.

Comandos suportados:
  INICIAR / OI / OLÁ  → Fluxo de cadastro e boas-vindas
  PRÓXIMA             → Avança para a próxima lição
  REPETIR             → Reenvia a lição atual
  AJUDA               → Lista de comandos disponíveis
  PARAR               → Cancela o recebimento de aulas
  NÍVEL               → Informa/altera o nível atual
  [áudio]             → Feedback de pronúncia com IA
  [texto livre]       → Resposta conversacional com IA

Idioma fixo: Inglês 🇬🇧 (configurado via ACTIVE_LANG no .env)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .evolution_client import EvolutionClient
    from .student_manager import StudentManager, SUPPORTED_LANGS
    from .lesson_curriculum import LessonCurriculum
    from .scheduler import LessonScheduler

logger = logging.getLogger(__name__)

# ─────────────────────────── Constants ───────────────────────────────────────

# Idioma ativo — lido do ambiente para permitir troca sem alterar código
import os as _os
ACTIVE_LANG: str = _os.environ.get("ACTIVE_LANG", "en")

WELCOME_MSG = """🎓 *Bem-vindo(a) ao Shadowing Practice!*

Olá! Sou seu assistente de *inglês* via WhatsApp. 🇬🇧
Vou te enviar *mini-aulas diárias* com frases autênticas, áudios de pronúncia e exercícios de shadowing — exatamente como o BeConfident!

🎯 *Qual é o seu nível atual de inglês?*

1️⃣  A1 — Iniciante (zero ou pouca experiência)
2️⃣  A2 — Básico (entendo palavras simples)
3️⃣  B1 — Intermediário (consigo me comunicar)
4️⃣  B2 — Médio-avançado (converso com confiança)

Responda com o *número* ou *código* (A1, A2, B1, B2)."""

LEVEL_MSG = """🎯 *Qual é o seu nível atual?*

1️⃣  A1 — Iniciante (zero experiência)
2️⃣  A2 — Básico (entendo palavras simples)
3️⃣  B1 — Intermediário (consigo me comunicar)
4️⃣  B2 — Médio-avançado (converso com confiança)

Responda com o *número* ou *código de nível* (A1, A2, B1, B2)."""

HELP_MSG = """📋 *Comandos disponíveis:*

🔄  *PRÓXIMA* — Próxima lição
🔁  *REPETIR* — Repetir lição atual
📊  *NÍVEL* — Ver/alterar nível
📈  *PROGRESSO* — Ver seu progresso
🔊  *VOZ ON* — Ativar respostas em áudio
🔇  *VOZ OFF* — Desativar respostas em áudio
⏸️  *PARAR* — Pausar mini-aulas
▶️  *INICIAR* — Reativar mini-aulas
❓  *AJUDA* — Esta mensagem

🎤 *Envie um áudio* para receber feedback de pronúncia!
💬 *Envie uma mensagem* para conversar em inglês."""

STOP_MSG = """⏸️ Mini-aulas pausadas.

Quando quiser retomar, envie *INICIAR*.
Seus dados e progresso estão salvos.

Até logo! 👋"""

RESUME_MSG = """▶️ *Mini-aulas reativadas!*

Ótimo ter você de volta! 🎉
Sua próxima lição chegará no próximo horário agendado.

Para receber uma lição *agora*, envie *PRÓXIMA*."""



LEVEL_CHOICE = {
    "1": "A1", "a1": "A1",
    "2": "A2", "a2": "A2",
    "3": "B1", "b1": "B1",
    "4": "B2", "b2": "B2",
}

START_WORDS = {"iniciar", "oi", "olá", "ola", "hello", "hi", "hola", "bonjour", "ciao", "hallo", "start"}
NEXT_WORDS = {"próxima", "proxima", "next", "siguiente", "suivant", "nächste", "prossima", "avançar"}
REPEAT_WORDS = {"repetir", "repeat", "de novo", "novamente", "again", "otra vez"}
STOP_WORDS = {"parar", "stop", "cancelar", "desativar", "sair", "exit", "unsubscribe"}
RESUME_WORDS = {"iniciar", "start", "reativar", "ativar", "continuar", "retomar"}
PROGRESS_WORDS = {"progresso", "progress", "estatísticas", "estatisticas", "stats"}
VOICE_ON_WORDS = {"voz on", "audio on", "falar on", "voice on", "ligar voz", "voz ligada"}
VOICE_OFF_WORDS = {"voz off", "audio off", "falar off", "voice off", "desligar voz", "voz desligada"}


class WhatsAppHandler:
    """Processa eventos do webhook e coordena respostas."""

    def __init__(
        self,
        client: "EvolutionClient",
        students: "StudentManager",
        curriculum: "LessonCurriculum",
        scheduler: "LessonScheduler",
        ai_feedback_fn: Any = None,
        ai_chat_fn: Any = None,
        ai_tts_fn: Any = None,
    ) -> None:
        self.client = client
        self.students = students
        self.curriculum = curriculum
        self.scheduler = scheduler
        self.ai_feedback = ai_feedback_fn  # Opcional: função para feedback de áudio com IA
        self.ai_chat = ai_chat_fn  # Opcional: função de conversa IA por texto
        self.ai_tts = ai_tts_fn  # Opcional: função TTS IA (retorna áudio base64 OGG)

    # ─────────────────────── Webhook entry point ─────────────────────────────

    def handle_event(self, event: dict) -> dict:
        """Ponto de entrada principal para eventos do webhook."""
        event_type = str(event.get("event", "") or "").strip()
        event_key = event_type.lower().replace("-", "_").replace(".", "_")

        if event_key == "messages_upsert":
            return self._handle_message(event)

        return {"ok": True, "action": "ignored", "event": event_type}

    # ─────────────────────── Message routing ─────────────────────────────────

    def _handle_message(self, event: dict) -> dict:
        data = event.get("data", {}) or {}

        # Ignorar mensagens enviadas pelo próprio bot
        key = data.get("key", {}) or {}
        if key.get("fromMe"):
            return {"ok": True, "action": "skipped_own_message"}

        phone = self._extract_phone(key.get("remoteJid", ""), data=data)
        if not phone:
            return {"ok": False, "error": "Could not extract phone number"}

        # Normaliza legado: quando webhook traz @lid mas também temos número real,
        # desativa registros antigos para evitar envios duplicados em schedulers.
        remote_jid = str(key.get("remoteJid", "") or "").strip().lower()
        if remote_jid.endswith("@lid"):
            lid_digits = remote_jid.split("@", 1)[0]
            if lid_digits and lid_digits != phone and self.students.exists(lid_digits):
                self.students.update(lid_digits, active=False)
            if self.students.exists(remote_jid):
                self.students.update(remote_jid, active=False)

        push_name = data.get("pushName", "")
        message = data.get("message", {})
        message_type = data.get("messageType", "")

        # Registra a resposta do aluno
        if self.students.exists(phone):
            self.students.record_reply(phone)

        # Roteamento por tipo de mensagem
        if message_type in {"audioMessage", "pttMessage"}:
            return self._handle_audio_message(phone, push_name, message, data)

        text = self._extract_text(message)
        if text:
            return self._handle_text_message(phone, push_name, text.strip())

        return {"ok": True, "action": "ignored_unsupported_type"}

    # ─────────────────────── Text message handler ────────────────────────────

    def _handle_text_message(self, phone: str, name: str, text: str) -> dict:
        text_lc = text.lower().strip()
        student = self.students.get(phone)

        # ── Fluxo de cadastro pendente ──────────────────────────────────────
        if student and student.get("pending_level_choice"):
            return self._handle_level_choice(phone, text_lc)

        # ── Novo usuário ────────────────────────────────────────────────────
        if not student or text_lc in START_WORDS:
            if not student:
                self.students.register(phone, name=name, lang=ACTIVE_LANG)
            self.students.update(phone, pending_level_choice=True, pending_lang_choice=False)
            self.client.send_text(phone, WELCOME_MSG)
            return {"ok": True, "action": "welcome_sent"}

        # ── Aluno inativo voltando ───────────────────────────────────────────
        if not student.get("active") and text_lc in RESUME_WORDS:
            self.students.update(phone, active=True)
            self.client.send_text(phone, RESUME_MSG)
            return {"ok": True, "action": "resumed"}

        # ── Comandos principais ──────────────────────────────────────────────
        if text_lc in STOP_WORDS:
            self.students.deactivate(phone)
            self.client.send_text(phone, STOP_MSG)
            return {"ok": True, "action": "stopped"}

        if text_lc in NEXT_WORDS:
            max_idx = self.curriculum.total(student.get("lang", "en"))
            self.students.advance_lesson(phone, max_idx)
            result = self.scheduler.send_now(phone)
            return {"ok": True, "action": "next_lesson", "result": result}

        if text_lc in REPEAT_WORDS:
            result = self.scheduler.send_now(phone)
            return {"ok": True, "action": "repeat_lesson", "result": result}

        if text_lc == "ajuda" or text_lc == "help":
            self.client.send_text(phone, HELP_MSG)
            return {"ok": True, "action": "help_sent"}

        if text_lc in {"nível", "nivel", "level"}:
            self.students.update(phone, pending_level_choice=True)
            self.client.send_text(phone, LEVEL_MSG)
            return {"ok": True, "action": "level_change_prompted"}

        if text_lc in PROGRESS_WORDS:
            return self._send_progress(phone, student)

        if text_lc in VOICE_ON_WORDS:
            self.students.update(phone, voice_responses=True)
            self.client.send_text(
                phone,
                "🔊 Respostas em áudio ativadas.\n\nAgora eu vou responder com texto + voz."
            )
            return {"ok": True, "action": "voice_enabled"}

        if text_lc in VOICE_OFF_WORDS:
            self.students.update(phone, voice_responses=False)
            self.client.send_text(
                phone,
                "🔇 Respostas em áudio desativadas.\n\nContinuo respondendo em texto normalmente."
            )
            return {"ok": True, "action": "voice_disabled"}

        # ── Conversa livre com IA (texto) ────────────────────────────────────
        return self._handle_free_text(phone, student, text)

    # ─────────────────────── Audio message handler ───────────────────────────

    def _handle_audio_message(self, phone: str, name: str, message: dict, data: dict) -> dict:
        student = self.students.get(phone)
        if not student:
            self.students.register(phone, name=name, lang=ACTIVE_LANG)
            self.students.update(phone, pending_level_choice=True)
            self.client.send_text(phone, WELCOME_MSG)
            return {"ok": True, "action": "welcome_sent_on_audio"}

        lang = student.get("lang", "en")
        index = int(student.get("lesson_index", 0))
        lesson = self.curriculum.get(lang, index)

        if not lesson:
            self.client.send_text(phone, "Não encontrei a lição atual. Envie *PRÓXIMA* para continuar.")
            return {"ok": False, "error": "lesson_not_found"}

        # Feedback sem IA — resposta padrão de incentivo
        feedback = (
            f"✅ *Ótimo trabalho!*\n\n"
            f"Você praticou: _{lesson.phrase}_\n\n"
            f"🎯 *Lembre-se:*\n"
            f"{lesson.tip}\n\n"
            f"🔄 Continue treinando! Envie *PRÓXIMA* para a próxima lição."
        )

        # Se tiver integração com IA para transcrição/feedback
        if self.ai_feedback:
            try:
                msg = data.get("message", {}) or {}
                audio_msg = msg.get("audioMessage") or msg.get("pttMessage") or {}
                audio_url = audio_msg.get("url", "")
                if audio_url or audio_msg:
                    try:
                        ai_result = self.ai_feedback(
                            audio_url=audio_url,
                            expected_phrase=lesson.phrase,
                            lang=lang,
                            lesson=lesson.to_dict() if hasattr(lesson, "to_dict") else {},
                            message_data=data,
                            audio_message=audio_msg,
                        )
                    except TypeError:
                        # Compatibilidade com assinatura antiga (audio_url, expected_phrase, lang)
                        ai_result = self.ai_feedback(
                            audio_url=audio_url,
                            expected_phrase=lesson.phrase,
                            lang=lang,
                        )

                    if ai_result and ai_result.get("feedback"):
                        feedback = ai_result["feedback"]

                    raw_score = (ai_result or {}).get("score")
                    if raw_score is not None:
                        try:
                            score = max(1, min(100, int(round(float(raw_score)))))
                        except Exception:
                            score = None
                        if score is not None:
                            prev_samples = int(student.get("pronunciation_samples", 0) or 0)
                            prev_avg = float(student.get("pronunciation_avg_score", 0) or 0)
                            samples = prev_samples + 1
                            avg = (
                                ((prev_avg * prev_samples) + score) / samples
                                if prev_samples > 0
                                else float(score)
                            )
                            self.students.update(
                                phone,
                                pronunciation_last_score=score,
                                pronunciation_avg_score=round(avg, 1),
                                pronunciation_samples=samples,
                            )
            except Exception as exc:
                logger.warning("AI feedback failed: %s", exc)

        self.client.send_text(phone, feedback)
        if bool(student.get("voice_responses", True)):
            self._send_voice_message(
                phone,
                lesson.phrase,
                lang=lang,
            )
        return {"ok": True, "action": "audio_feedback_sent"}

    # ─────────────────────── Onboarding flows ────────────────────────────────

    def _handle_level_choice(self, phone: str, text_lc: str) -> dict:
        level = LEVEL_CHOICE.get(text_lc)
        if not level:
            self.client.send_text(
                phone,
                "❓ Não entendi. Responda: *1* (A1) | *2* (A2) | *3* (B1) | *4* (B2)"
            )
            return {"ok": True, "action": "level_choice_retry"}

        self.students.update(phone, level=level, pending_level_choice=False)

        lang_name = "Inglês 🇬🇧"

        confirm_msg = (
            f"🎉 *Perfeito! Você está cadastrado(a)!*\n\n"
            f"📚 Idioma: *{lang_name}*\n"
            f"📊 Nível: *{level}*\n\n"
            f"📅 Você receberá mini-aulas automaticamente às:\n"
            f"🌅 *9h00* e 🌆 *19h00* (horário de Brasília)\n\n"
            f"Envie *PRÓXIMA* para receber sua primeira lição agora!\n"
            f"Ou aguarde o próximo horário programado.\n\n"
            f"_Use *AJUDA* a qualquer momento para ver os comandos._"
        )
        self.client.send_text(phone, confirm_msg)
        return {"ok": True, "action": "onboarding_complete", "level": level}

    # ─────────────────────── Helpers ─────────────────────────────────────────

    def _send_progress(self, phone: str, student: dict) -> dict:
        lang = student.get("lang", ACTIVE_LANG)
        total = self.curriculum.total(lang)
        pron_samples = int(student.get("pronunciation_samples", 0) or 0)
        pron_avg = student.get("pronunciation_avg_score", "")
        pron_last = student.get("pronunciation_last_score", "")
        pron_line = ""
        if pron_samples > 0:
            pron_line = (
                f"🎤 Pronúncia: média {pron_avg}/100 "
                f"(última {pron_last}/100, {pron_samples} áudios)\n"
            )
        voice_status = "ON 🔊" if bool(student.get("voice_responses", True)) else "OFF 🔇"
        msg = (
            f"📈 *Seu Progresso*\n\n"
            f"👤 Nome: {student.get('name','?')}\n"
            f"📚 Idioma: Inglês 🇬🇧\n"
            f"📊 Nível: {student.get('level','?')}\n"
            f"🗣️ Resposta em voz: {voice_status}\n"
            f"🔥 Sequência: {student.get('streak',0)} dias\n"
            f"📖 Lições enviadas: {student.get('total_lessons_sent',0)}\n"
            f"💬 Respostas enviadas: {student.get('total_replies',0)}\n"
            f"{pron_line}"
            f"📋 Lição atual: {student.get('lesson_index',0)+1}/{total}\n\n"
            f"_Continue treinando! Consistência é a chave._ 🗝️"
        )
        self.client.send_text(phone, msg)
        return {"ok": True, "action": "progress_sent"}

    def _handle_free_text(self, phone: str, student: dict, text: str) -> dict:
        lang = student.get("lang", "en")
        reply = (
            "👏 Boa! Vamos treinar de forma prática.\n\n"
            "Tente responder em inglês em 1-2 frases.\n"
            "Exemplo: _Today I practiced English for 15 minutes._\n\n"
            "Me manda sua resposta e eu te corrijo. 🎯"
        )
        voice_text = ""

        if self.ai_chat:
            try:
                ai_result = self.ai_chat(
                    user_text=text,
                    student=student,
                    lang=lang,
                )
                if isinstance(ai_result, dict):
                    ai_reply = str(ai_result.get("reply", "")).strip()
                    ai_voice = str(ai_result.get("voice_text", "")).strip()
                    if ai_reply:
                        reply = ai_reply
                    if ai_voice:
                        voice_text = ai_voice
            except Exception as exc:
                logger.warning("AI chat reply failed: %s", exc)

        self.client.send_text(phone, reply)
        voice_sent = False
        if bool(student.get("voice_responses", True)):
            voice_sent = self._send_voice_message(
                phone,
                voice_text or reply,
                lang=lang,
            )
        return {"ok": True, "action": "free_text_response", "voice_sent": voice_sent}

    def _send_voice_message(self, phone: str, text: str, *, lang: str = "en") -> bool:
        text = str(text or "").strip()
        if not text:
            return False
        try:
            if self.ai_tts:
                try:
                    tts_result = self.ai_tts(text=text, lang=lang)
                except TypeError:
                    tts_result = self.ai_tts(text, lang)

                audio_b64 = ""
                ai_engine = ""
                if isinstance(tts_result, dict):
                    audio_b64 = str(tts_result.get("audio_b64") or tts_result.get("audio") or "").strip()
                    ai_engine = str(tts_result.get("engine") or "").strip()
                elif isinstance(tts_result, str):
                    audio_b64 = tts_result.strip()

                if audio_b64:
                    if ai_engine:
                        logger.info("Voice response via %s", ai_engine)
                    result = self.client.send_audio_b64(phone, audio_b64, ptt=True)
                    if isinstance(result, dict) and not result.get("error"):
                        return True

            if not hasattr(self.scheduler, "_generate_audio"):
                return False
            audio_b64 = self.scheduler._generate_audio(text, lang)  # noqa: SLF001
            if not audio_b64:
                return False
            result = self.client.send_audio_b64(phone, audio_b64, ptt=True)
            return isinstance(result, dict) and not result.get("error")
        except Exception as exc:
            logger.warning("Voice response failed: %s", exc)
            return False

    @staticmethod
    def _extract_phone(jid: str, data: dict | None = None) -> str:
        """Extrai o melhor identificador de contato para responder.

        Prioriza JIDs reais do WhatsApp (`@s.whatsapp.net`) e evita usar
        IDs `@lid` quando houver uma alternativa melhor no payload.
        """
        data = data or {}
        key = data.get("key", {}) if isinstance(data.get("key"), dict) else {}
        candidates: list[str] = []

        def _add(value: Any) -> None:
            text = str(value or "").strip()
            if not text:
                return
            if text not in candidates:
                candidates.append(text)

        _add(jid)
        _add(key.get("remoteJid"))
        _add(key.get("participant"))
        _add(data.get("sender"))
        _add(data.get("senderPnJid"))
        _add(data.get("participant"))
        _add(data.get("remoteJid"))
        _add(data.get("from"))
        _add(data.get("jid"))
        _add(data.get("chatId"))

        def _rank(candidate: str) -> int:
            cand_lc = candidate.lower()
            if cand_lc.endswith("@s.whatsapp.net") or cand_lc.endswith("@c.us"):
                return 100
            if re.fullmatch(r"\d{8,20}", candidate):
                return 80
            if cand_lc.endswith("@lid"):
                return 60
            if cand_lc.endswith("@g.us"):
                return 5
            return 20

        best = ""
        best_rank = -1
        for candidate in candidates:
            rank = _rank(candidate)
            if rank > best_rank:
                best = candidate
                best_rank = rank

        if not best:
            return ""

        best_lc = best.lower()
        if best_lc.endswith("@s.whatsapp.net") or best_lc.endswith("@c.us"):
            return best.split("@", 1)[0]
        if "@" in best:
            return best
        if re.fullmatch(r"\d{8,20}", best):
            return best

        match = re.match(r"(\d+)@", best)
        return match.group(1) if match else ""

    @staticmethod
    def _extract_text(message: dict) -> str:
        """Extrai texto de diferentes tipos de mensagem."""
        return (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or message.get("listResponseMessage", {}).get("title")
            or message.get("buttonsResponseMessage", {}).get("selectedDisplayText")
            or ""
        )
