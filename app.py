"""
Shadowing Practice for Fluency — Backend
=========================================
Aplicação web com voz natural (LMNT) e análise inteligente (DeepSeek/OpenRouter/OpenAI/Ollama).

APIs:
  - LMNT (https://lmnt.com) → Text-to-Speech com vozes ultra-realistas
  - DeepSeek (https://api.deepseek.com) → IA textual compatível com OpenAI
  - OpenRouter (https://openrouter.ai) → IA para análise de texto, dicas de pronúncia
  - OpenAI Chat (https://api.openai.com) → fallback adicional para IA textual
  - Ollama local (http://127.0.0.1:11434) → fallback de IA textual sem token
  - Piper TTS (local/offline) → fallback principal sem API externa
  - YouTube Search → Busca de vídeos virais relacionados
"""

import os
import json
import ast
import uuid
import re
import time
import csv
import io
import base64
import threading
import html
import difflib
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import sys
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests as http_requests
from flask import (
    Flask, render_template, request, jsonify,
    url_for, Response
)
from youtube_search import YoutubeSearch
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest
from agents import AgentOrchestrator, ToolRegistry, ToolResult
from adaptive_learning import AdaptiveLearningStore, LearnerContext, DEFAULT_DATABASE_URL

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None

try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

# ──────────────────────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────────────────────
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "static" / "audio"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_FILE = DATA_DIR / "progress.json"
HISTORY_FILE = DATA_DIR / "session_history.json"
if not PROGRESS_FILE.exists():
    PROGRESS_FILE.write_text("[]", encoding="utf-8")
if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]", encoding="utf-8")

# Limite de arquivos de áudio (auto-cleanup)
AUDIO_MAX_AGE_HOURS = 24
AUDIO_MAX_FILES = 100

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip()
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OLLAMA_ENABLED = (
    os.getenv("OLLAMA_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip()
OLLAMA_TIMEOUT_SEC = max(
    5,
    int(os.getenv("OLLAMA_TIMEOUT_SEC", "90") or "90"),
)
LMNT_API_KEY = os.getenv("LMNT_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")
DEEPGRAM_TTS_MODEL = os.getenv("DEEPGRAM_TTS_MODEL", "").strip()
DEEPGRAM_ENABLED = (
    os.getenv("DEEPGRAM_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
)
DEEPGRAM_TTS_TIMEOUT_SEC = max(
    5,
    int(os.getenv("DEEPGRAM_TTS_TIMEOUT_SEC", "45") or "45"),
)
OPENROUTER_AUDIO_MODEL = os.getenv(
    "OPENROUTER_AUDIO_MODEL",
    "openrouter/auto",
)
LOCAL_WHISPER_ENABLED = (
    os.getenv("LOCAL_WHISPER_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
)
LOCAL_WHISPER_MODEL = os.getenv("LOCAL_WHISPER_MODEL", "tiny")
LOCAL_WHISPER_DEVICE = os.getenv("LOCAL_WHISPER_DEVICE", "cpu")
LOCAL_WHISPER_COMPUTE_TYPE = os.getenv("LOCAL_WHISPER_COMPUTE_TYPE", "int8")

# Piper TTS (offline/local)
PIPER_ENABLED = (
    os.getenv("PIPER_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
)
PIPER_MODEL_PATH_EN = Path(
    os.getenv(
        "PIPER_MODEL_PATH_EN",
        str(BASE_DIR / "models" / "en_US-amy-medium.onnx"),
    )
)
PIPER_MODEL_PATH_PT = Path(
    os.getenv(
        "PIPER_MODEL_PATH_PT",
        str(BASE_DIR / "models" / "pt_BR-faber-medium.onnx"),
    )
)
PIPER_MODEL_PATH_FR = Path(
    os.getenv(
        "PIPER_MODEL_PATH_FR",
        str(BASE_DIR / "models" / "fr_FR-siwis-medium.onnx"),
    )
)
PIPER_MODEL_PATH_ES = Path(
    os.getenv(
        "PIPER_MODEL_PATH_ES",
        str(BASE_DIR / "models" / "es_ES-sharvard-medium.onnx"),
    )
)
PIPER_MODEL_PATH_DE = Path(
    os.getenv(
        "PIPER_MODEL_PATH_DE",
        str(BASE_DIR / "models" / "de_DE-thorsten-medium.onnx"),
    )
)
PIPER_MODEL_PATH_IT = Path(
    os.getenv(
        "PIPER_MODEL_PATH_IT",
        str(BASE_DIR / "models" / "it_IT-paola-medium.onnx"),
    )
)
PIPER_MODEL_PATHS = {
    "en": PIPER_MODEL_PATH_EN,
    "pt": PIPER_MODEL_PATH_PT,
    "fr": PIPER_MODEL_PATH_FR,
    "es": PIPER_MODEL_PATH_ES,
    "de": PIPER_MODEL_PATH_DE,
    "it": PIPER_MODEL_PATH_IT,
}
PIPER_CORE_LANGS = tuple(PIPER_MODEL_PATHS.keys())
PIPER_TIMEOUT_SEC = max(
    5,
    int(os.getenv("PIPER_TIMEOUT_SEC", "60") or "60"),
)
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip()

# LMNT endpoints
LMNT_SPEECH_URL = "https://api.lmnt.com/v1/ai/speech/bytes"
LMNT_SPEECH_DETAILED_URL = "https://api.lmnt.com/v1/ai/speech"
LMNT_VOICES_URL = "https://api.lmnt.com/v1/ai/voice/list"
DEEPGRAM_SPEAK_URL = "https://api.deepgram.com/v1/speak"

# OpenRouter endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
_LOCAL_WHISPER_MODEL_CACHE = None
_DATA_LOCK = threading.Lock()
_OLLAMA_MODEL_CACHE = {"name": "", "checked_at": 0.0}
_AGENT_ORCHESTRATOR = None
_ADAPTIVE_STORE = AdaptiveLearningStore(DATABASE_URL)

# ── WhatsApp Mini-Lesson components (lazy-init) ──────────────────────────────
_WA_CLIENT = None
_WA_STUDENTS = None
_WA_CURRICULUM = None
_WA_SCHEDULER = None
_WA_HANDLER = None
_WA_LOCK = threading.Lock()
WHATSAPP_ENABLED = (
    os.getenv("WHATSAPP_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
)

SUPPORTED_LANGS = {"en", "pt", "es", "fr", "de", "it", "ja", "ko", "zh"}
STUDY_TARGET_LANGS = {"pt", "en", "es", "fr", "de", "it"}
PRACTICE_LANG_LABELS = {
    "en": "English",
    "pt": "Português",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
}
DEEPGRAM_TTS_MODELS_BY_LANG = {
    "en": "aura-2-thalia-en",
    "es": "aura-2-celeste-es",
    "fr": "aura-2-agathe-fr",
    "de": "aura-2-viktoria-de",
    "it": "aura-2-livia-it",
    "ja": "aura-2-izanami-ja",
    "nl": "aura-2-rhea-nl",
}
PRACTICE_LENGTH_RULES = {
    "micro": {"label": "Micro", "sentences": "1-2 frases curtas", "min": 1, "max": 2},
    "short": {"label": "Curto", "sentences": "3-4 frases", "min": 3, "max": 4},
    "medium": {"label": "Médio", "sentences": "5-6 frases", "min": 5, "max": 6},
    "long": {"label": "Longo", "sentences": "7-9 frases", "min": 7, "max": 9},
}
PRACTICE_TYPE_LABELS = {
    "dialogue": "diálogo natural entre duas pessoas",
    "monologue": "monólogo curto (uma pessoa falando)",
    "story": "mini história narrativa",
    "interview": "simulação de entrevista",
    "presentation": "apresentação explicativa curta",
    "casual_chat": "conversa casual do dia a dia",
}
HISTORY_RETENTION = 50
PROGRESS_RETENTION = 500
MAX_TEXT_CHARS = 5000
MAX_QUERY_CHARS = 180
MAX_TOPIC_CHARS = 160
MAX_FOCUS_CHARS = 220
MAX_STUDY_SEGMENTS = 18
MAX_STUDY_WORDS = 6

PIPER_LEXICON_PATH = Path(
    os.getenv(
        "PIPER_LEXICON_PATH",
        str(CONFIG_DIR / "piper_pronunciations.json"),
    )
)
PIPER_VOICE_OVERRIDES_PATH = Path(
    os.getenv(
        "PIPER_VOICE_OVERRIDES_PATH",
        str(CONFIG_DIR / "piper_voice_profiles.json"),
    )
)
PIPER_CONTEXTUAL_ENABLED = (
    os.getenv("PIPER_CONTEXTUAL_ENABLED", "1").strip().lower()
    not in {"0", "false", "no"}
)
PIPER_POSTPROCESS_ENABLED = (
    os.getenv("PIPER_POSTPROCESS_ENABLED", "1").strip().lower()
    not in {"0", "false", "no"}
)
PIPER_POSTPROCESS_FILTER = os.getenv(
    "PIPER_POSTPROCESS_FILTER",
    "highpass=f=55,lowpass=f=7600,afftdn=nf=-24:tn=1",
).strip()
PIPER_POSTPROCESS_TIMEOUT_SEC = max(
    5,
    int(os.getenv("PIPER_POSTPROCESS_TIMEOUT_SEC", "25") or "25"),
)
PIPER_PROSODY_BASE_BY_LANG = {
    "default": {
        "length_scale": 1.0,
        "noise_scale": 0.56,
        "noise_w_scale": 0.62,
        "sentence_silence": 0.14,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "en": {
        "length_scale": 0.98,
        "noise_scale": 0.58,
        "noise_w_scale": 0.64,
        "sentence_silence": 0.12,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "pt": {
        "length_scale": 1.0,
        "noise_scale": 0.54,
        "noise_w_scale": 0.60,
        "sentence_silence": 0.14,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "es": {
        "length_scale": 0.99,
        "noise_scale": 0.56,
        "noise_w_scale": 0.62,
        "sentence_silence": 0.13,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "fr": {
        "length_scale": 1.01,
        "noise_scale": 0.53,
        "noise_w_scale": 0.59,
        "sentence_silence": 0.14,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "de": {
        "length_scale": 1.02,
        "noise_scale": 0.53,
        "noise_w_scale": 0.59,
        "sentence_silence": 0.14,
        "volume": 1.0,
        "normalize_audio": False,
    },
    "it": {
        "length_scale": 1.0,
        "noise_scale": 0.55,
        "noise_w_scale": 0.61,
        "sentence_silence": 0.13,
        "volume": 1.0,
        "normalize_audio": False,
    },
}
PIPER_PROFILE_ADJUSTMENTS = {
    "balanced": {},
    "chat": {
        "length_scale": -0.04,
        "noise_scale": 0.02,
        "noise_w_scale": 0.01,
        "sentence_silence": -0.05,
    },
    "lesson": {
        "length_scale": 0.06,
        "noise_scale": -0.04,
        "noise_w_scale": -0.05,
        "sentence_silence": 0.04,
    },
    "story": {
        "length_scale": 0.04,
        "noise_scale": -0.02,
        "noise_w_scale": -0.02,
        "sentence_silence": 0.07,
    },
    "question": {
        "length_scale": -0.01,
        "noise_scale": 0.0,
        "noise_w_scale": 0.02,
        "sentence_silence": -0.03,
    },
    "expressive": {
        "length_scale": -0.03,
        "noise_scale": 0.03,
        "noise_w_scale": 0.04,
        "sentence_silence": -0.02,
        "volume": 0.02,
    },
}
PIPER_PROFILE_LABELS = {
    "balanced": "geral",
    "chat": "conversa",
    "lesson": "didatico",
    "story": "narracao",
    "question": "pergunta",
    "expressive": "expressivo",
}
PIPER_DEFAULT_PROFILE_BY_CONTEXT = {
    "conversation_reply": "chat",
    "single_phrase": "lesson",
    "study_phrase": "lesson",
    "shadowing_sentence": "lesson",
    "shadowing_practice_session": "story",
    "youtube_study_phrase": "lesson",
}
PIPER_QUESTION_PREFIXES = {
    "en": (
        "who ",
        "what ",
        "why ",
        "when ",
        "where ",
        "how ",
        "do ",
        "does ",
        "did ",
        "is ",
        "are ",
        "can ",
        "could ",
        "would ",
        "should ",
        "will ",
        "have ",
        "has ",
    ),
    "pt": (
        "quem ",
        "como ",
        "quando ",
        "onde ",
        "qual ",
        "quais ",
        "quanto ",
        "quantos ",
        "por que ",
        "porque ",
        "o que ",
        "que ",
        "pode ",
        "poderia ",
        "vai ",
    ),
    "es": (
        "quien ",
        "como ",
        "cuando ",
        "donde ",
        "cual ",
        "cuanto ",
        "por que ",
        "que ",
        "puede ",
        "podria ",
    ),
    "fr": (
        "qui ",
        "quoi ",
        "comment ",
        "quand ",
        "ou ",
        "pourquoi ",
        "est-ce que ",
        "peux ",
        "pouvez ",
        "voudrais ",
    ),
    "de": (
        "wer ",
        "was ",
        "wie ",
        "wann ",
        "wo ",
        "warum ",
        "kann ",
        "kannst ",
        "können ",
        "möchtest ",
    ),
    "it": (
        "chi ",
        "cosa ",
        "come ",
        "quando ",
        "dove ",
        "perché ",
        "quale ",
        "quanto ",
        "puoi ",
        "potresti ",
        "vuoi ",
    ),
}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def _write_json_atomic(path: Path, payload):
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(serialized)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _require_json_object() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Envie um JSON válido no corpo da requisição.")
    if not isinstance(data, dict):
        raise BadRequest("O JSON da requisição deve ser um objeto.")
    return data


def _normalize_text_field(
    value,
    field_name: str,
    *,
    required: bool = True,
    max_chars: int = MAX_TEXT_CHARS,
) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise BadRequest(f"{field_name} não pode estar vazio.")
    if len(text) > max_chars:
        raise BadRequest(f"{field_name} excede o limite de {max_chars} caracteres.")
    return text


def _normalize_lang(value, default: str = "en") -> str:
    lang = str(value or default).strip().lower()
    if not lang:
        return default
    return lang if lang in SUPPORTED_LANGS else default


def _normalize_practice_lang(value, default: str = "en") -> str:
    raw = str(value or default).strip().lower().replace("_", "-")
    aliases = {
        "pt-br": "pt",
        "pt-pt": "pt",
        "en-us": "en",
        "en-gb": "en",
        "es-es": "es",
        "fr-fr": "fr",
        "de-de": "de",
        "it-it": "it",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in STUDY_TARGET_LANGS else default


def _normalize_practice_length(value, default: str = "medium") -> str:
    length = str(value or default).strip().lower()
    return length if length in PRACTICE_LENGTH_RULES else default


def _normalize_practice_type(value, default: str = "dialogue") -> str:
    raw = str(value or default).strip().lower().replace("-", "_")
    aliases = {
        "conversation": "dialogue",
        "chat": "casual_chat",
        "casual": "casual_chat",
        "narrative": "story",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in PRACTICE_TYPE_LABELS else default


def _split_sentences_for_practice(text: str) -> list[str]:
    cleaned = _clean_caption_text(text or "")
    if not cleaned:
        return []

    # Tenta primeiro segmentar por pontuação + espaço.
    primary = [
        part.strip()
        for part in re.split(r'(?<=[.!?。！？])\s+', cleaned)
        if part.strip()
    ]
    if len(primary) > 1:
        return primary

    # Fallback para idiomas que podem não usar espaço após pontuação.
    secondary = [
        part.strip()
        for part in re.split(r'(?<=[.!?。！？])\s*', cleaned)
        if part.strip()
    ]
    return secondary if secondary else [cleaned]


def _enforce_practice_text_length(text: str, length_key: str) -> str:
    rules = PRACTICE_LENGTH_RULES.get(length_key) or PRACTICE_LENGTH_RULES["medium"]
    max_sentences = int(rules.get("max") or 6)
    parts = _split_sentences_for_practice(text)
    if not parts:
        return text
    if len(parts) <= max_sentences:
        return " ".join(parts).strip()
    return " ".join(parts[:max_sentences]).strip()


def _analysis_word_key(token: str) -> str:
    key = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9']+", "", str(token or "")).strip().strip("'")
    return key.casefold()


def _analysis_text_words(text: str, *, min_len: int = 2, limit: int = 220) -> list[str]:
    words = []
    seen = set()
    for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", text or ""):
        key = _analysis_word_key(token)
        if len(key) < min_len or key in seen:
            continue
        seen.add(key)
        words.append(token)
        if len(words) >= limit:
            break
    return words


def _analysis_text_sentences(text: str) -> list[str]:
    raw = _clean_caption_text(text or "")
    if not raw:
        return []
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?。！？])\s+", raw)
        if item.strip()
    ]
    return sentences if sentences else [raw]


def _analysis_normalize_phrase_for_match(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        re.sub(r"[^\w']+", " ", str(text or "").casefold(), flags=re.UNICODE),
    ).strip()


def _analysis_find_sentence_for_word(sentences: list[str], word_key: str) -> str:
    for sentence in sentences:
        tokens = {
            _analysis_word_key(token)
            for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", sentence or "")
        }
        if word_key in tokens:
            return sentence
    return ""


def _normalize_ai_analysis(raw_analysis, source_text: str, source_lang: str) -> dict:
    source_lang = _normalize_lang(source_lang, default="en")
    sentences = _analysis_text_sentences(source_text)
    allowed_words = _analysis_text_words(source_text, min_len=2, limit=260)
    allowed_by_key = {_analysis_word_key(word): word for word in allowed_words}
    source_norm = f" {_analysis_normalize_phrase_for_match(source_text)} "

    payload = raw_analysis if isinstance(raw_analysis, dict) else {}

    raw_level = str(payload.get("difficulty_level", "") or "").strip().lower()
    if raw_level not in {"beginner", "intermediate", "advanced"}:
        total_words = max(1, len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", source_text or "")))
        if total_words <= 35:
            raw_level = "beginner"
        elif total_words <= 95:
            raw_level = "intermediate"
        else:
            raw_level = "advanced"

    score_default = {"beginner": 2, "intermediate": 3, "advanced": 4}[raw_level]
    difficulty_score = _coerce_int(
        payload.get("difficulty_score"),
        default=score_default,
        min_value=1,
        max_value=5,
    )

    pronunciation_tips = []
    seen_pron = set()
    for item in payload.get("pronunciation_tips") or []:
        if not isinstance(item, dict):
            continue
        word_key = _analysis_word_key(item.get("word", ""))
        if not word_key or word_key not in allowed_by_key or word_key in seen_pron:
            continue
        seen_pron.add(word_key)
        word = allowed_by_key[word_key]
        phonetic = _clean_caption_text(item.get("phonetic") or item.get("ipa") or "")
        if phonetic.casefold() in {"ipa", "fonetica", "phonetic", "pronunciation"}:
            phonetic = ""
        tip = _clean_caption_text(item.get("tip") or item.get("note") or "")
        if not tip:
            tip = f"Repita '{word}' com ritmo natural e atenção à sílaba tônica."
        pronunciation_tips.append({
            "word": word,
            "phonetic": phonetic,
            "tip": tip,
        })
        if len(pronunciation_tips) >= 6:
            break

    if not pronunciation_tips:
        for word in allowed_words:
            key = _analysis_word_key(word)
            if len(key) < 4:
                continue
            pronunciation_tips.append({
                "word": word,
                "phonetic": "",
                "tip": f"Repita '{word}' com clareza e ligue esta palavra à próxima.",
            })
            if len(pronunciation_tips) >= 5:
                break

    linking_sounds = []
    seen_linking = set()
    for item in payload.get("linking_sounds") or []:
        if not isinstance(item, dict):
            continue
        phrase = _clean_caption_text(item.get("phrase") or item.get("text") or "")
        phrase_norm = _analysis_normalize_phrase_for_match(phrase)
        if len(phrase_norm.split()) < 2:
            continue
        if f" {phrase_norm} " not in source_norm:
            continue
        if phrase_norm in seen_linking:
            continue
        seen_linking.add(phrase_norm)
        linking_sounds.append({
            "phrase": phrase,
            "how": _clean_caption_text(item.get("how") or item.get("pronunciation") or ""),
            "tip": _clean_caption_text(item.get("tip") or item.get("note") or "") or "Conecte os sons finais e iniciais sem pausas longas.",
        })
        if len(linking_sounds) >= 5:
            break

    key_vocabulary = []
    seen_vocab = set()
    for item in payload.get("key_vocabulary") or []:
        if not isinstance(item, dict):
            continue
        word_key = _analysis_word_key(item.get("word", ""))
        if not word_key or word_key not in allowed_by_key or word_key in seen_vocab:
            continue
        seen_vocab.add(word_key)
        word = allowed_by_key[word_key]
        meaning = _clean_caption_text(item.get("meaning") or item.get("translation") or "")
        if not meaning:
            meaning = "Significado contextual em português."
        example = _clean_caption_text(item.get("example") or "")
        if not example or _analysis_word_key(word) not in {
            _analysis_word_key(token)
            for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", example or "")
        }:
            example = _analysis_find_sentence_for_word(sentences, word_key)
        key_vocabulary.append({
            "word": word,
            "meaning": meaning,
            "example": example,
        })
        if len(key_vocabulary) >= 8:
            break

    if not key_vocabulary:
        seed_words = [item["word"] for item in pronunciation_tips[:6]]
        for word in seed_words:
            word_key = _analysis_word_key(word)
            key_vocabulary.append({
                "word": word,
                "meaning": "Significado contextual em português.",
                "example": _analysis_find_sentence_for_word(sentences, word_key),
            })

    intonation_notes = _clean_caption_text(payload.get("intonation_notes") or "")
    if not intonation_notes:
        intonation_notes = (
            "Mantenha ritmo estável, destaque palavras de conteúdo "
            "e reduza palavras funcionais para soar mais natural."
        )

    shadowing_focus = []
    seen_focus = set()
    for item in payload.get("shadowing_focus") or []:
        focus = _clean_caption_text(item)
        focus_norm = _analysis_normalize_phrase_for_match(focus)
        if not focus_norm or focus_norm in seen_focus:
            continue
        is_single = len(focus_norm.split()) == 1
        if is_single and focus_norm not in allowed_by_key:
            continue
        if not is_single and f" {focus_norm} " not in source_norm:
            continue
        seen_focus.add(focus_norm)
        shadowing_focus.append(focus)
        if len(shadowing_focus) >= 5:
            break

    if len(shadowing_focus) < 3:
        for item in pronunciation_tips:
            word = item.get("word", "")
            key = _analysis_word_key(word)
            if not word or key in seen_focus:
                continue
            seen_focus.add(key)
            shadowing_focus.append(word)
            if len(shadowing_focus) >= 5:
                break
    if len(shadowing_focus) < 3:
        for item in key_vocabulary:
            word = _clean_caption_text(item.get("word", ""))
            key = _analysis_word_key(word)
            if not word or key in seen_focus:
                continue
            seen_focus.add(key)
            shadowing_focus.append(word)
            if len(shadowing_focus) >= 5:
                break

    common_mistakes = []
    seen_mistakes = set()
    for item in payload.get("common_mistakes_br") or []:
        text = _clean_caption_text(item)
        key = text.casefold()
        if not text or key in seen_mistakes:
            continue
        seen_mistakes.add(key)
        common_mistakes.append(text)
        if len(common_mistakes) >= 6:
            break

    if not common_mistakes and source_lang == "en":
        common_mistakes = [
            "Evite traduzir mentalmente palavra por palavra enquanto fala.",
            "Não leia todas as palavras com o mesmo peso; use sílabas tônicas.",
            "Conecte palavras curtas para manter ritmo natural.",
        ]

    return {
        "difficulty_level": raw_level,
        "difficulty_score": difficulty_score,
        "pronunciation_tips": pronunciation_tips,
        "linking_sounds": linking_sounds,
        "key_vocabulary": key_vocabulary,
        "intonation_notes": intonation_notes,
        "shadowing_focus": shadowing_focus[:5],
        "common_mistakes_br": common_mistakes,
    }


def _coerce_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "sim"}:
            return True
        if normalized in {"0", "false", "no", "off", "nao", "não"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _normalize_tts_engine(value, *, use_lmnt=None, default: str = "local") -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    aliases = {
        "lmnt": "lmnt",
        "deepgram": "deepgram",
        "dg": "deepgram",
        "local": "local",
        "piper": "local",
    }
    if raw in aliases:
        return aliases[raw]
    if use_lmnt is not None:
        return "lmnt" if _coerce_bool(use_lmnt, default=False) else "local"
    return aliases.get(default, "local")


def _coerce_int(value, default: int, min_value: int, max_value: int) -> int:
    try:
        coerced = int(float(value))
    except (TypeError, ValueError):
        coerced = default
    return max(min_value, min(max_value, coerced))


def _safe_csv_cell(value) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _normalize_learner_key(value, default: str = "web-default") -> str:
    raw = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    if not raw:
        return default
    normalized = re.sub(r"[^a-z0-9:_-]+", "-", raw).strip("-")
    return normalized or default


def _build_learner_context(
    data: dict | None = None,
    *,
    default_lang: str = "en",
    channel: str = "web",
    default_level: str = "A1",
) -> LearnerContext:
    payload = data if isinstance(data, dict) else {}
    learner_key = _normalize_learner_key(
        payload.get("learner_key")
        or request.headers.get("X-Learner-Key")
        or request.args.get("learner_key"),
        default="web-default",
    )
    learner_name = re.sub(
        r"\s+",
        " ",
        str(
            payload.get("learner_name")
            or request.headers.get("X-Learner-Name")
            or request.args.get("learner_name")
            or ""
        ),
    ).strip()[:120]
    learner_level = re.sub(
        r"\s+",
        " ",
        str(
            payload.get("level")
            or payload.get("learner_level")
            or request.headers.get("X-Learner-Level")
            or request.args.get("level")
            or default_level
        ),
    ).strip()[:16] or default_level
    target_lang = _normalize_lang(
        payload.get("target_lang")
        or payload.get("lang")
        or request.args.get("lang")
        or default_lang,
        default=default_lang,
    )
    external_user_id = (
        payload.get("external_user_id")
        or payload.get("user_id")
        or request.headers.get("X-External-User-Id")
        or request.args.get("external_user_id")
        or request.args.get("user_id")
    )
    try:
        external_user_id = int(str(external_user_id).strip()) if str(external_user_id or "").strip() else None
    except (TypeError, ValueError):
        external_user_id = None
    external_email = re.sub(
        r"\s+",
        " ",
        str(
            payload.get("external_email")
            or payload.get("email")
            or payload.get("user_email")
            or request.headers.get("X-External-User-Email")
            or request.args.get("external_email")
            or request.args.get("email")
            or ""
        ),
    ).strip()[:254]
    external_phone = re.sub(
        r"\s+",
        " ",
        str(
            payload.get("external_phone")
            or payload.get("phone")
            or payload.get("phone_number")
            or request.headers.get("X-External-Phone")
            or request.args.get("external_phone")
            or request.args.get("phone")
            or ""
        ),
    ).strip()[:32]
    source_system = re.sub(
        r"\s+",
        " ",
        str(
            payload.get("source_system")
            or request.headers.get("X-Source-System")
            or request.args.get("source_system")
            or "shadowing_practice"
        ),
    ).strip()[:40] or "shadowing_practice"
    return LearnerContext(
        learner_key=learner_key,
        channel=channel,
        display_name=learner_name,
        target_lang=target_lang,
        level=learner_level,
        native_lang="pt",
        source_system=source_system,
        external_user_id=external_user_id,
        external_email=external_email,
        external_phone=external_phone,
    )


def _serialize_progress_entry(entry: dict) -> dict:
    if not isinstance(entry, dict):
        return {}
    date_value = str(entry.get("date", "") or "")
    if isinstance(entry.get("date"), date):
        date_value = entry["date"].isoformat()
    return {
        "id": int(entry.get("id") or 0) if str(entry.get("id") or "").strip() else 0,
        "date": date_value,
        "material": str(entry.get("material", "") or ""),
        "duration_min": _coerce_int(entry.get("duration_min", 0), default=0, min_value=0, max_value=720),
        "repetitions": _coerce_int(entry.get("repetitions", 0), default=0, min_value=0, max_value=300),
        "difficulty": _coerce_int(entry.get("difficulty", 3), default=3, min_value=1, max_value=5),
        "notes": str(entry.get("notes", "") or ""),
    }


def _adaptive_dashboard_for_request(*, default_lang: str = "en") -> dict:
    learner = _build_learner_context({}, default_lang=default_lang)
    dashboard = _ADAPTIVE_STORE.get_dashboard(
        learner,
        fallback_lang=learner.target_lang,
    )
    dashboard.setdefault("learner", {})
    dashboard.setdefault("summary", {})
    dashboard["adaptive_enabled"] = bool(_ADAPTIVE_STORE.enabled)
    if _ADAPTIVE_STORE.last_error:
        dashboard["adaptive_warning"] = _ADAPTIVE_STORE.last_error
    return dashboard


def _load_progress() -> list:
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError, PermissionError, OSError):
        return []


def _save_progress(entries: list):
    _write_json_atomic(PROGRESS_FILE, entries[-PROGRESS_RETENTION:])


def _load_history() -> list:
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    except (PermissionError, OSError):
        # Arquivo pode ficar com owner root em execuções via container.
        # Mantemos a API funcional e tentamos recriar em seguida.
        try:
            _write_json_atomic(HISTORY_FILE, [])
        except Exception:
            pass
        return []


def _save_history(entries: list):
    # Keep only last sessions configured by HISTORY_RETENTION
    _write_json_atomic(HISTORY_FILE, entries[-HISTORY_RETENTION:])


def _clean_text_for_search(text: str, max_words: int = 10) -> str:
    words = text.split()
    return " ".join(words[:max_words])


def _normalize_search_query(query: str, max_chars: int = MAX_QUERY_CHARS) -> str:
    cleaned = re.sub(r"\s+", " ", str(query or "")).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].strip()
    return cleaned


def _default_youtube_query(lang: str) -> str:
    defaults = {
        "en": "english speaking practice viral",
        "pt": "ingles conversacao pratica",
        "es": "espanol conversacion practica",
        "fr": "francais conversation pratique",
        "de": "deutsch sprechen uebung",
        "it": "italiano conversazione pratica",
    }
    return defaults.get(lang, "language speaking practice")


def _format_youtube_duration(value) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, (int, float)):
        return ""
    total = max(0, int(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _format_youtube_views(value) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, (int, float)):
        return ""
    count = max(0, int(value))
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B views"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M views"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K views"
    return f"{count} views"


def _normalize_youtube_thumbnails(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        url = str(value.get("url", "")).strip()
        return [url] if url else []
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if isinstance(item, str):
            thumb = item.strip()
        elif isinstance(item, dict):
            thumb = str(item.get("url", "")).strip()
        else:
            thumb = ""
        if thumb:
            normalized.append(thumb)
    return normalized


def _normalize_youtube_video_entry(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None

    video_id = str(raw.get("id", "")).strip()
    if not video_id:
        possible_url = str(
            raw.get("url")
            or raw.get("webpage_url")
            or raw.get("webpage_url_basename")
            or ""
        ).strip()
        video_id = _extract_youtube_video_id(possible_url)
    if not video_id:
        return None

    title = str(raw.get("title", "")).strip() or "YouTube Video"
    duration = _format_youtube_duration(raw.get("duration"))
    views = _format_youtube_views(raw.get("views") or raw.get("view_count"))
    channel = str(raw.get("channel") or raw.get("uploader") or "").strip()
    thumbnails = _normalize_youtube_thumbnails(raw.get("thumbnails"))

    return {
        "id": video_id,
        "title": title,
        "duration": duration,
        "views": views,
        "channel": channel,
        "thumbnails": thumbnails,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "embed_url": f"https://www.youtube.com/embed/{video_id}",
    }


def _search_videos_with_youtube_search(query: str, max_results: int) -> list[dict]:
    results = YoutubeSearch(query, max_results=max_results).to_dict()
    videos = []
    for entry in results:
        normalized = _normalize_youtube_video_entry(entry)
        if normalized:
            videos.append(normalized)
    return videos[:max_results]


def _search_videos_with_ytdlp(query: str, max_results: int) -> list[dict]:
    if yt_dlp is None:
        return []

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

    entries = info.get("entries") if isinstance(info, dict) else []
    videos = []
    for entry in entries or []:
        normalized = _normalize_youtube_video_entry(entry)
        if normalized:
            videos.append(normalized)
    return videos[:max_results]


def _search_youtube_videos(
    query: str,
    *,
    lang: str = "en",
    max_results: int = 6,
    allow_generic_fallback: bool = True,
) -> tuple[list[dict], str, str]:
    attempts = []
    cleaned = _normalize_search_query(query)
    if cleaned:
        attempts.append(cleaned)

    if allow_generic_fallback:
        generic = _default_youtube_query(lang)
        if generic and generic not in attempts:
            attempts.append(generic)

    if not attempts:
        return [], "", "query vazia"

    last_error = ""
    for candidate in attempts:
        try:
            videos = _search_videos_with_youtube_search(candidate, max_results=max_results)
        except Exception as exc:
            last_error = f"youtube_search falhou em '{candidate}': {exc}"
            continue
        if videos:
            return videos, "youtube_search", ""
        last_error = f"youtube_search sem resultados em '{candidate}'."

    if yt_dlp is not None:
        for candidate in attempts:
            try:
                videos = _search_videos_with_ytdlp(candidate, max_results=max_results)
            except Exception as exc:
                last_error = f"yt_dlp falhou em '{candidate}': {exc}"
                continue
            if videos:
                return videos, "yt_dlp", ""
            last_error = f"yt_dlp sem resultados em '{candidate}'."

    return [], "", last_error or "falha desconhecida na busca do YouTube"


def _cleanup_old_audio(max_age_hours: int = AUDIO_MAX_AGE_HOURS,
                       max_files: int = AUDIO_MAX_FILES):
    """Remove arquivos de áudio antigos para evitar acúmulo em disco."""
    now = time.time()
    max_age_sec = max_age_hours * 3600
    files = sorted(AUDIO_DIR.glob("*.*"), key=lambda f: f.stat().st_mtime)

    removed = 0
    for f in files:
        if f.name == ".gitkeep":
            continue
        age = now - f.stat().st_mtime
        if age > max_age_sec or len(files) - removed > max_files:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass

    if removed:
        print(f"[Cleanup] Removidos {removed} arquivo(s) de áudio antigos.")
    return removed


def _get_audio_stats() -> dict:
    """Retorna estatísticas da pasta de áudio."""
    files = [f for f in AUDIO_DIR.glob("*.*") if f.name != ".gitkeep"]
    total_size = sum(f.stat().st_size for f in files)
    return {
        "file_count": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "shadows": len([f for f in files if f.name.startswith("shadow_")]),
        "phrases": len([f for f in files if f.name.startswith("phrase_")]),
        "recordings": len([f for f in files if f.name.startswith("recording_")]),
    }


def _detect_language(text: str) -> str:
    en_words = {"the", "is", "are", "was", "were", "have", "has", "do",
                "does", "will", "would", "can", "could", "should", "a",
                "an", "and", "or", "but", "in", "on", "at", "to", "for"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    en_count = len(words & en_words)
    return "en" if en_count >= 2 else "pt"


def _extract_youtube_video_id(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if YOUTUBE_ID_RE.fullmatch(value):
        return value

    patterns = (
        r"(?:https?://)?(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?[^#\s]*v=([A-Za-z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/live/([A-Za-z0-9_-]{11})",
    )
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return ""


def _get_snippet_value(snippet, key: str, default=None):
    if isinstance(snippet, dict):
        return snippet.get(key, default)
    return getattr(snippet, key, default)


def _normalize_transcript_segments(raw_snippets) -> list[dict]:
    segments = []
    for item in raw_snippets or []:
        text = str(_get_snippet_value(item, "text", "") or "")
        text = re.sub(r"\s+", " ", text.replace("\n", " ").strip())
        if not text:
            continue

        # Remove marcador curto de ruído, ex.: [Music], [Applause]
        if re.fullmatch(r"[\[\(][^)\]]{1,24}[\]\)]", text) and len(text.split()) <= 3:
            continue

        try:
            start = float(_get_snippet_value(item, "start", 0.0) or 0.0)
            duration = float(_get_snippet_value(item, "duration", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue

        duration = max(0.18, duration)
        end = start + duration
        segment = {
            "text": text,
            "start": round(start, 3),
            "duration": round(duration, 3),
            "end": round(end, 3),
        }
        if isinstance(item, dict):
            words = _normalize_word_timings(item.get("words") or [], start, end)
            if words:
                segment["words"] = words
        segments.append(segment)
    return segments


def _merge_transcript_segments(segments: list[dict],
                               max_gap: float = 0.35,
                               max_chars: int = 96) -> list[dict]:
    if not segments:
        return []

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        gap = seg["start"] - prev["end"]
        can_merge = gap <= max_gap and len(prev["text"]) + 1 + len(seg["text"]) <= max_chars
        if can_merge:
            prev["text"] = f"{prev['text']} {seg['text']}"
            prev["end"] = seg["end"]
            prev["duration"] = round(prev["end"] - prev["start"], 3)
            if prev.get("words") or seg.get("words"):
                prev["words"] = (prev.get("words") or []) + (seg.get("words") or [])
        else:
            merged.append(seg.copy())
    return merged


def _is_terminal_sentence_punctuation(text: str) -> bool:
    text = str(text or "").strip()
    if not text:
        return True
    return bool(re.search(r"[.!?…][\"')\]]*$", text))


def _starts_like_new_sentence(text: str) -> bool:
    text = str(text or "").lstrip()
    if not text:
        return False
    return bool(re.match(r"^[A-ZÀ-ÖØ-Þ]", text))


def _merge_sentence_like_segments(segments: list[dict],
                                  max_gap: float = 0.22,
                                  max_chars: int = 220,
                                  max_duration: float = 20.0) -> list[dict]:
    if not segments:
        return []

    ordered = sorted(segments, key=lambda s: (s["start"], s["end"]))
    merged = [ordered[0].copy()]

    for seg in ordered[1:]:
        current = seg.copy()
        prev = merged[-1]
        gap = current["start"] - prev["end"]
        combined_duration = current["end"] - prev["start"]
        combined_text = f"{prev['text']} {current['text']}".strip()

        likely_same_sentence = (
            not _is_terminal_sentence_punctuation(prev["text"])
            or not _starts_like_new_sentence(current["text"])
        )
        has_room = len(combined_text) <= max_chars and combined_duration <= max_duration

        if gap <= max_gap and likely_same_sentence and has_room:
            prev["text"] = combined_text
            prev["end"] = current["end"]
            prev["duration"] = round(prev["end"] - prev["start"], 3)
            if prev.get("words") or current.get("words"):
                prev["words"] = (prev.get("words") or []) + (current.get("words") or [])
        else:
            merged.append(current)

    return merged


def _dedupe_overlapping_segments(segments: list[dict],
                                 max_start_delta: float = 0.16,
                                 overlap_tolerance: float = 0.25) -> list[dict]:
    if not segments:
        return []

    deduped = []
    for seg in sorted(segments, key=lambda s: (s["start"], s["end"])):
        current = seg.copy()
        if not deduped:
            deduped.append(current)
            continue

        prev = deduped[-1]
        same_text = current["text"].strip().casefold() == prev["text"].strip().casefold()
        start_close = abs(current["start"] - prev["start"]) <= max_start_delta
        overlaps = current["start"] <= (prev["end"] + overlap_tolerance)

        if same_text and (start_close or overlaps):
            if current["end"] > prev["end"]:
                prev["end"] = current["end"]
                prev["duration"] = round(prev["end"] - prev["start"], 3)
            if current.get("words"):
                prev["words"] = (prev.get("words") or []) + (current.get("words") or [])
            continue

        deduped.append(current)

    return deduped


def _pick_youtube_transcript(transcript_list, preferred_lang: str):
    preferred_lang = (preferred_lang or "en").strip().lower()
    preferred = []
    if preferred_lang:
        preferred.extend([preferred_lang, preferred_lang.replace("_", "-")])
    if "en" not in preferred:
        preferred.extend(["en", "en-US", "en-GB", "en-CA", "en-AU"])
    preferred = list(dict.fromkeys(preferred))

    for lang in preferred:
        try:
            return transcript_list.find_manually_created_transcript([lang])
        except Exception:
            pass

    for lang in preferred:
        try:
            return transcript_list.find_generated_transcript([lang])
        except Exception:
            pass

    # Fallback: primeiro transcript disponível
    for transcript in transcript_list:
        return transcript
    return None


def _list_youtube_transcripts(video_id: str):
    if YouTubeTranscriptApi is None:
        raise RuntimeError(
            "Dependência 'youtube-transcript-api' não instalada no ambiente."
        )

    # Compatibilidade com versões antigas e novas da biblioteca.
    if hasattr(YouTubeTranscriptApi, "list_transcripts"):
        return YouTubeTranscriptApi.list_transcripts(video_id)

    api = YouTubeTranscriptApi()
    if hasattr(api, "list"):
        return api.list(video_id)

    raise RuntimeError(
        "Versão de 'youtube-transcript-api' incompatível: método de listagem não encontrado."
    )


def _fetch_youtube_transcript(video_id: str, preferred_lang: str = "en") -> dict:
    if YouTubeTranscriptApi is None:
        raise RuntimeError(
            "Dependência 'youtube-transcript-api' não instalada no ambiente."
        )

    transcript_list = _list_youtube_transcripts(video_id)
    transcript = _pick_youtube_transcript(transcript_list, preferred_lang)
    if transcript is None:
        raise ValueError("Nenhuma transcrição disponível para este vídeo.")

    requested_lang = (preferred_lang or "").strip().lower()
    lang_code = (getattr(transcript, "language_code", "") or "").lower()
    if (
        requested_lang
        and requested_lang not in lang_code
        and getattr(transcript, "is_translatable", False)
    ):
        try:
            transcript = transcript.translate(requested_lang)
        except Exception:
            pass

    fetched = transcript.fetch()
    if hasattr(fetched, "to_raw_data"):
        raw_snippets = fetched.to_raw_data()
    elif isinstance(fetched, list):
        raw_snippets = fetched
    else:
        raw_snippets = list(fetched)

    segments = _normalize_transcript_segments(raw_snippets)
    segments = _dedupe_overlapping_segments(segments)
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.18, max_chars=210, max_duration=14.5
    )
    if not segments:
        raise ValueError("Transcrição vazia ou inválida para este vídeo.")

    word_count = sum(len(seg["text"].split()) for seg in segments)
    total_duration = max(seg["end"] for seg in segments)
    return {
        "segments": segments,
        "language_code": getattr(transcript, "language_code", ""),
        "language": getattr(transcript, "language", ""),
        "is_generated": bool(getattr(transcript, "is_generated", False)),
        "source": "youtube_transcript_api",
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_duration, 2),
        },
    }


def _fetch_youtube_oembed(video_id: str) -> dict:
    oembed_url = (
        "https://www.youtube.com/oembed"
        f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
    )
    try:
        resp = http_requests.get(oembed_url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", ""),
                "author_name": data.get("author_name", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
            }
    except Exception:
        pass
    return {}


def _build_caption_language_preferences(preferred_lang: str) -> list[str]:
    preferred_lang = (preferred_lang or "en").strip().lower()
    prefs = []
    if preferred_lang:
        prefs.extend([preferred_lang, preferred_lang.replace("_", "-")])
    if "en" not in prefs:
        prefs.extend(["en", "en-us", "en-gb", "en-ca", "en-au"])
    return list(dict.fromkeys([p for p in prefs if p]))


def _find_caption_entries(caption_map: dict, lang_prefs: list[str]) -> tuple[str, list] | tuple[None, None]:
    if not caption_map:
        return None, None

    normalized = {str(k).lower(): v for k, v in caption_map.items() if v}

    # 1) Match exato
    for pref in lang_prefs:
        if pref in normalized:
            return pref, normalized[pref]

    # 2) Match por prefixo (ex: en -> en-orig)
    for pref in lang_prefs:
        for lang, entries in normalized.items():
            if lang.startswith(pref):
                return lang, entries

    # 3) Fallback: primeira opção disponível
    first_lang = next(iter(normalized.keys()))
    return first_lang, normalized[first_lang]


def _pick_best_caption_entry(entries: list[dict]) -> dict | None:
    if not entries:
        return None

    ext_priority = {"json3": 0, "srv1": 1, "vtt": 2, "ttml": 3}
    ranked = sorted(
        entries,
        key=lambda e: (ext_priority.get(str(e.get("ext", "")).lower(), 99), len(str(e.get("name", ""))))
    )
    for entry in ranked:
        if entry.get("url"):
            return entry
    return None


def _download_text_from_url(url: str, timeout: int = 20) -> str:
    resp = http_requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _clean_caption_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_timestamp_to_seconds(raw: str) -> float:
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return 0.0

    # Suporta 00:01:02.345 e 01:02.345
    parts = raw.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600 + float(m) * 60 + float(s)
        if len(parts) == 2:
            m, s = parts
            return float(m) * 60 + float(s)
        return float(parts[0])
    except ValueError:
        return 0.0


def _parse_ttml_time_to_seconds(raw: str) -> float:
    raw = (raw or "").strip()
    if not raw:
        return 0.0
    if raw.endswith("ms"):
        try:
            return float(raw[:-2]) / 1000.0
        except ValueError:
            return 0.0
    if raw.endswith("s"):
        try:
            return float(raw[:-1])
        except ValueError:
            return 0.0
    return _parse_timestamp_to_seconds(raw)


def _parse_vtt_segments(vtt_text: str) -> list[dict]:
    segments = []
    lines = (vtt_text or "").replace("\r", "").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue

        try:
            start_raw, end_raw = [p.strip() for p in line.split("-->", 1)]
            start = _parse_timestamp_to_seconds(start_raw.split(" ")[0])
            end = _parse_timestamp_to_seconds(end_raw.split(" ")[0])
        except Exception:
            i += 1
            continue

        i += 1
        cue_lines = []
        while i < len(lines) and lines[i].strip():
            cue_lines.append(lines[i].strip())
            i += 1
        text = _clean_caption_text(" ".join(cue_lines))
        if text:
            duration = max(0.18, end - start)
            segments.append({
                "text": text,
                "start": start,
                "duration": duration,
            })
        i += 1
    return segments


def _parse_json3_segments(json_text: str) -> list[dict]:
    segments = []
    try:
        data = json.loads(json_text or "{}")
    except json.JSONDecodeError:
        return []

    events = data.get("events", []) or []
    for idx, event in enumerate(events):
        segs = event.get("segs") or []
        text = _clean_caption_text("".join(s.get("utf8", "") for s in segs))
        if not text:
            continue

        start = float(event.get("tStartMs", 0) or 0) / 1000.0
        duration = float(event.get("dDurationMs", 0) or 0) / 1000.0
        if duration <= 0:
            next_start_ms = None
            if idx + 1 < len(events):
                next_start_ms = events[idx + 1].get("tStartMs")
            if next_start_ms is not None:
                duration = max(0.18, (float(next_start_ms) / 1000.0) - start)
            else:
                duration = 1.0

        segments.append({
            "text": text,
            "start": start,
            "duration": max(0.18, duration),
        })
    return segments


def _parse_srv1_segments(xml_text: str) -> list[dict]:
    segments = []
    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError:
        return []

    for node in root.findall(".//text"):
        text = _clean_caption_text("".join(node.itertext()))
        if not text:
            continue
        try:
            start = float(node.attrib.get("start", 0))
            duration = float(node.attrib.get("dur", 1.0))
        except ValueError:
            continue
        segments.append({
            "text": text,
            "start": start,
            "duration": max(0.18, duration),
        })
    return segments


def _parse_ttml_segments(ttml_text: str) -> list[dict]:
    segments = []
    try:
        root = ET.fromstring(ttml_text or "")
    except ET.ParseError:
        return []

    for node in root.iter():
        tag = str(node.tag).lower()
        if not tag.endswith("p"):
            continue

        text = _clean_caption_text("".join(node.itertext()))
        if not text:
            continue

        begin = node.attrib.get("begin")
        end = node.attrib.get("end")
        dur = node.attrib.get("dur")
        start = _parse_ttml_time_to_seconds(begin)
        if end:
            finish = _parse_ttml_time_to_seconds(end)
            duration = max(0.18, finish - start)
        elif dur:
            duration = max(0.18, _parse_ttml_time_to_seconds(dur))
        else:
            duration = 1.0

        segments.append({
            "text": text,
            "start": start,
            "duration": duration,
        })
    return segments


def _parse_caption_payload(payload: str, ext: str) -> list[dict]:
    ext = (ext or "").strip().lower()
    if ext == "json3":
        return _parse_json3_segments(payload)
    if ext == "srv1":
        return _parse_srv1_segments(payload)
    if ext in ("ttml", "xml"):
        return _parse_ttml_segments(payload)
    return _parse_vtt_segments(payload)


def _guess_audio_content_type(audio_path: Path) -> str:
    ext = audio_path.suffix.lstrip(".").lower()
    return {
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "mp4": "audio/mp4",
        "aac": "audio/aac",
        "wav": "audio/wav",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "opus": "audio/ogg",
        "flac": "audio/flac",
    }.get(ext, "application/octet-stream")


def _normalize_word_timings(words, segment_start: float, segment_end: float) -> list[dict]:
    normalized = []
    start_bound = float(segment_start or 0.0)
    end_bound = float(segment_end or start_bound + 0.18)
    if end_bound <= start_bound:
        end_bound = start_bound + 0.18

    for item in words or []:
        if not isinstance(item, dict):
            continue
        text = _clean_caption_text(
            item.get("word")
            or item.get("text")
            or item.get("punctuated_word")
            or ""
        )
        if not text:
            continue
        try:
            w_start = float(item.get("start", 0.0))
            w_end = float(item.get("end", 0.0))
        except (TypeError, ValueError):
            continue
        w_start = max(start_bound, min(end_bound, w_start))
        w_end = max(w_start + 0.02, min(end_bound, w_end))
        normalized.append({
            "word": text,
            "start": round(w_start, 3),
            "end": round(w_end, 3),
        })

    normalized.sort(key=lambda w: w["start"])
    return normalized


def _join_words_for_segment(words: list[str]) -> str:
    text = " ".join(words)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _segment_deepgram_word_stream(words) -> list[dict]:
    word_entries = []
    for item in words or []:
        if not isinstance(item, dict):
            continue
        token = _clean_caption_text(item.get("punctuated_word") or item.get("word") or "")
        if not token:
            continue
        try:
            w_start = float(item.get("start", 0.0))
            w_end = float(item.get("end", 0.0))
        except (TypeError, ValueError):
            continue
        if w_end <= w_start:
            continue
        word_entries.append({
            "word": token,
            "start": w_start,
            "end": w_end,
        })

    if not word_entries:
        return []

    segments = []
    current = [word_entries[0]]
    for item in word_entries[1:]:
        prev = current[-1]
        gap = item["start"] - prev["end"]
        sentence_break = bool(re.search(r"[.!?]$", prev["word"]))
        too_long = len(current) >= 14
        if gap > 0.85 or sentence_break or too_long:
            segments.append(current)
            current = [item]
        else:
            current.append(item)
    if current:
        segments.append(current)

    raw_segments = []
    for chunk in segments:
        chunk_words = [w["word"] for w in chunk]
        chunk_text = _join_words_for_segment(chunk_words)
        if not chunk_text:
            continue
        start = chunk[0]["start"]
        end = chunk[-1]["end"]
        raw_segments.append({
            "text": chunk_text,
            "start": start,
            "duration": max(0.18, end - start),
            "words": chunk,
        })
    return raw_segments


def _deepgram_payload_to_raw_segments(payload: dict) -> tuple[list[dict], str]:
    results = payload.get("results") if isinstance(payload, dict) else {}
    if not isinstance(results, dict):
        results = {}

    utterances = results.get("utterances") or []
    raw_segments = []
    for utt in utterances:
        if not isinstance(utt, dict):
            continue
        text = _clean_caption_text(utt.get("transcript", ""))
        try:
            start = float(utt.get("start", 0.0) or 0.0)
            end = float(utt.get("end", start + 0.18) or (start + 0.18))
        except (TypeError, ValueError):
            continue
        if end <= start:
            end = start + 0.18

        words = _normalize_word_timings(utt.get("words") or [], start, end)
        if not text and words:
            text = _join_words_for_segment([w["word"] for w in words])
        if not text:
            continue
        seg = {
            "text": text,
            "start": start,
            "duration": max(0.18, end - start),
        }
        if words:
            seg["words"] = words
        raw_segments.append(seg)

    channels = results.get("channels") or []
    primary_alt = None
    if isinstance(channels, list) and channels and isinstance(channels[0], dict):
        alternatives = channels[0].get("alternatives") or []
        if isinstance(alternatives, list) and alternatives and isinstance(alternatives[0], dict):
            primary_alt = alternatives[0]

    detected_language = ""
    if isinstance(primary_alt, dict):
        detected_language = str(primary_alt.get("detected_language") or "").strip()
    metadata = payload.get("metadata") if isinstance(payload, dict) else {}
    if not detected_language and isinstance(metadata, dict):
        detected_language = str(metadata.get("detected_language") or "").strip()

    if raw_segments:
        return raw_segments, detected_language

    if isinstance(primary_alt, dict):
        alt_words = primary_alt.get("words") or []
        raw_segments = _segment_deepgram_word_stream(alt_words)
        if raw_segments:
            return raw_segments, detected_language

        transcript_text = _clean_caption_text(primary_alt.get("transcript", ""))
        if transcript_text:
            duration = 8.0
            if isinstance(metadata, dict):
                try:
                    duration = float(metadata.get("duration", 8.0) or 8.0)
                except (TypeError, ValueError):
                    duration = 8.0
            return ([{
                "text": transcript_text,
                "start": 0.0,
                "duration": max(0.18, duration),
            }], detected_language)

    return [], detected_language


def _fetch_youtube_transcript_with_deepgram(video_id: str, preferred_lang: str = "en") -> dict:
    if yt_dlp is None:
        raise RuntimeError("Dependência 'yt-dlp' não instalada para fallback Deepgram.")
    if not DEEPGRAM_API_KEY:
        raise RuntimeError("DEEPGRAM_API_KEY não configurada para fallback Deepgram.")

    with tempfile.TemporaryDirectory(prefix="yt_deepgram_") as tmp:
        tmp_dir = Path(tmp)
        outtmpl = str(tmp_dir / "%(id)s.%(ext)s")
        url = f"https://www.youtube.com/watch?v={video_id}"
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio[abr<=96]/worstaudio/worst",
            "outtmpl": outtmpl,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = _find_downloaded_audio_file(tmp_dir, info, ydl)

        if not audio_path or not audio_path.exists():
            raise ValueError("Não foi possível baixar o áudio para fallback Deepgram.")

        content_type = _guess_audio_content_type(audio_path)
        audio_bytes = audio_path.read_bytes()

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": content_type,
    }
    params = {
        "model": DEEPGRAM_MODEL,
        "smart_format": "true",
        "punctuate": "true",
        "utterances": "true",
    }
    lang = (preferred_lang or "").strip().lower().split("-")[0]
    if len(lang) == 2:
        params["language"] = lang

    resp = http_requests.post(
        "https://api.deepgram.com/v1/listen",
        headers=headers,
        params=params,
        data=audio_bytes,
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            "Falha no Deepgram transcription: "
            f"{resp.status_code} {resp.text[:220]}"
        )

    payload = resp.json()
    raw_segments, detected_language = _deepgram_payload_to_raw_segments(payload)
    segments = _normalize_transcript_segments(raw_segments)
    if not segments:
        raise ValueError("Deepgram retornou transcrição vazia.")

    if any(seg.get("words") for seg in segments):
        segments = sorted(segments, key=lambda s: s["start"])
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.22, max_chars=220, max_duration=18.0
    )

    word_count = sum(len(seg["text"].split()) for seg in segments)
    total_duration = max(seg["end"] for seg in segments)
    language = detected_language or lang or preferred_lang or ""
    return {
        "segments": segments,
        "language_code": language,
        "language": language,
        "is_generated": True,
        "source": "deepgram_stt",
        "timing_offset_sec": 0.0,
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_duration, 2),
        },
    }


def _fetch_youtube_transcript_with_ytdlp(video_id: str, preferred_lang: str = "en") -> dict:
    if yt_dlp is None:
        raise RuntimeError("Dependência 'yt-dlp' não instalada no ambiente.")

    url = f"https://www.youtube.com/watch?v={video_id}"
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    subtitles = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    lang_prefs = _build_caption_language_preferences(preferred_lang)

    lang_code, entries = _find_caption_entries(subtitles, lang_prefs)
    is_generated = False
    source = "yt_dlp_subtitles"

    if not entries:
        lang_code, entries = _find_caption_entries(automatic, lang_prefs)
        is_generated = True
        source = "yt_dlp_auto_captions"

    if not entries:
        raise ValueError("Nenhuma legenda encontrada via fallback yt-dlp.")

    entry = _pick_best_caption_entry(entries)
    if not entry:
        raise ValueError("Legenda encontrada, mas sem URL de download suportada.")

    payload = _download_text_from_url(entry["url"])
    raw_segments = _parse_caption_payload(payload, entry.get("ext", "vtt"))
    segments = _normalize_transcript_segments(raw_segments)
    segments = _dedupe_overlapping_segments(segments)
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.18, max_chars=210, max_duration=14.5
    )

    if not segments:
        raise ValueError("Falha ao interpretar as legendas do fallback yt-dlp.")

    word_count = sum(len(seg["text"].split()) for seg in segments)
    total_duration = max(seg["end"] for seg in segments)

    return {
        "segments": segments,
        "language_code": lang_code or preferred_lang or "",
        "language": lang_code or preferred_lang or "",
        "is_generated": is_generated,
        "source": source,
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_duration, 2),
        },
    }


def _coerce_json_like_payload(candidate: str) -> dict | None:
    raw = (candidate or "").strip()
    if not raw:
        return None

    def _wrap(data) -> dict | None:
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"segments": data}
        return None

    attempts = [raw]
    cleaned = raw
    cleaned = cleaned.replace("“", '"').replace("”", '"')
    cleaned = cleaned.replace("’", "'")
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    if cleaned != raw:
        attempts.append(cleaned)

    for snippet in attempts:
        try:
            parsed = json.loads(snippet)
            wrapped = _wrap(parsed)
            if wrapped is not None:
                return wrapped
        except json.JSONDecodeError:
            continue

    # Aceita quase-JSON (aspas simples / trailing comma) de forma segura.
    for snippet in attempts:
        py_like = re.sub(r"\btrue\b", "True", snippet, flags=re.IGNORECASE)
        py_like = re.sub(r"\bfalse\b", "False", py_like, flags=re.IGNORECASE)
        py_like = re.sub(r"\bnull\b", "None", py_like, flags=re.IGNORECASE)
        try:
            parsed = ast.literal_eval(py_like)
            wrapped = _wrap(parsed)
            if wrapped is not None:
                return wrapped
        except (ValueError, SyntaxError):
            continue
    return None


def _extract_json_payload_from_text(text: str) -> dict | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    direct = _coerce_json_like_payload(raw)
    if direct is not None:
        return direct

    # Try to parse any balanced JSON object/list embedded in text.
    starts = [i for i, ch in enumerate(raw) if ch in "{["]
    for start in starts:
        stack = []
        in_string = False
        escaped = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue
            if ch in "{[":
                stack.append(ch)
                continue
            if ch in "}]":
                if not stack:
                    break
                open_ch = stack.pop()
                if (open_ch == "{" and ch != "}") or (open_ch == "[" and ch != "]"):
                    break
                if not stack:
                    candidate = raw[start:i + 1].strip()
                    parsed = _coerce_json_like_payload(candidate)
                    if parsed is not None:
                        return parsed
                    break
    return None


def _extract_segment_dicts_from_text(text: str) -> list[dict]:
    raw = (text or "").strip()
    if not raw:
        return []

    # Collect balanced JSON objects and keep those that look like segment entries.
    candidates = []
    starts = [i for i, ch in enumerate(raw) if ch == "{"]
    for start in starts:
        stack = []
        in_string = False
        escaped = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                stack.append(ch)
                continue
            if ch == "}":
                if not stack:
                    break
                stack.pop()
                if not stack:
                    snippet = raw[start:i + 1]
                    try:
                        obj = json.loads(snippet)
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict):
                        has_text = isinstance(obj.get("text"), str) and bool(obj.get("text", "").strip())
                        has_time = any(k in obj for k in ("start", "end", "duration"))
                        if has_text and has_time:
                            candidates.append(obj)
                    break
    return candidates


def _coerce_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _shift_raw_segments(raw_segments: list[dict],
                        shift_sec: float,
                        total_duration: float = 0.0) -> list[dict]:
    shifted = []
    for seg in raw_segments:
        start = float(seg.get("start", 0.0) or 0.0) + shift_sec
        duration = float(seg.get("duration", 0.18) or 0.18)
        start = max(0.0, start)
        if total_duration > 0:
            start = min(start, total_duration)
            duration = min(max(0.18, duration), max(0.18, total_duration - start))
        else:
            duration = max(0.18, duration)
        shifted.append({
            "text": seg.get("text", ""),
            "start": start,
            "duration": duration,
        })
    return shifted


def _estimate_first_vocal_start_openrouter(audio_b64: str,
                                           audio_format: str,
                                           total_duration: float = 0.0) -> float | None:
    if not OPENROUTER_API_KEY:
        return None

    system_prompt = (
        "Return ONLY valid JSON: "
        '{"first_vocal_start_sec": 0.0}. '
        "Estimate when the first clearly audible singing or spoken lyric begins."
    )
    user_prompt = (
        "Analyze this audio and estimate the timestamp (in seconds) where vocals begin. "
        "Use video timeline from 0. If vocals start immediately, return near 0."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Shadowing Practice for Fluency",
    }
    payload = {
        "model": OPENROUTER_AUDIO_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": audio_format,
                        },
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 120,
    }

    try:
        resp = http_requests.post(
            OPENROUTER_URL,
            json=payload,
            headers=headers,
            timeout=120,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                c.get("text", "") if isinstance(c, dict) else str(c)
                for c in content
            )
        content = str(content or "").strip()

        parsed = _extract_json_payload_from_text(content) or {}
        value = _coerce_float(
            parsed.get("first_vocal_start_sec")
            or parsed.get("first_vocal_start")
            or parsed.get("vocal_start_sec")
        )
        if value is None:
            match = re.search(r"(-?\d+(?:\.\d+)?)", content)
            if match:
                value = _coerce_float(match.group(1))
        if value is None:
            return None
        if total_duration > 0:
            value = min(max(0.0, value), total_duration)
        else:
            value = max(0.0, value)
        return value
    except Exception:
        return None


def _text_to_timed_segments(text: str, total_duration: float = 0.0) -> list[dict]:
    text = _clean_caption_text(text)
    if not text:
        return []

    # If model leaked raw JSON as text, recover it instead of showing JSON karaoke.
    if ("segments" in text and "{" in text) or (text.startswith("[") and "\"start\"" in text):
        maybe = _extract_json_payload_from_text(text)
        parsed_segments = _model_payload_to_timed_segments(maybe or {}, total_duration)
        if parsed_segments:
            return parsed_segments

    lines = [l.strip() for l in re.split(r"[\n\r]+", text) if l.strip()]
    if len(lines) <= 1:
        lines = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(lines) <= 1:
        words = text.split()
        chunk = 8
        lines = [" ".join(words[i:i + chunk]) for i in range(0, len(words), chunk)]
        lines = [l for l in lines if l]

    if total_duration <= 0:
        total_duration = max(8.0, len(text.split()) / 2.8)

    weights = [max(1, len(re.sub(r"\s+", "", l))) for l in lines]
    total_weight = sum(weights) or len(lines)
    cursor = 0.0
    raw_segments = []
    for idx, line in enumerate(lines):
        is_last = idx == len(lines) - 1
        seg_duration = total_duration * (weights[idx] / total_weight)
        seg_duration = max(0.18, seg_duration)
        start = cursor
        end = total_duration if is_last else min(total_duration, cursor + seg_duration)
        if end <= start:
            end = start + 0.18
        raw_segments.append({
            "text": line,
            "start": start,
            "duration": end - start,
        })
        cursor = end

    return raw_segments


def _model_payload_to_timed_segments(payload_obj: dict,
                                     total_duration: float = 0.0) -> list[dict]:
    if not isinstance(payload_obj, dict):
        return []

    items = payload_obj.get("segments")
    if not isinstance(items, list):
        nested = payload_obj.get("data")
        if isinstance(nested, dict):
            items = nested.get("segments")
    if not isinstance(items, list):
        nested = payload_obj.get("result")
        if isinstance(nested, dict):
            items = nested.get("segments")
    if not isinstance(items, list) or not items:
        return []

    raw_segments = []
    last_end = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        text = _clean_caption_text(item.get("text", ""))
        if not text:
            continue

        start = item.get("start")
        end = item.get("end")
        duration = item.get("duration")
        try:
            start = float(start) if start is not None else last_end
        except (TypeError, ValueError):
            start = last_end

        if end is not None:
            try:
                end = float(end)
            except (TypeError, ValueError):
                end = None
        if duration is not None:
            try:
                duration = float(duration)
            except (TypeError, ValueError):
                duration = None

        if end is None:
            if duration is not None:
                end = start + duration
            else:
                end = start + 1.2

        if total_duration > 0:
            start = min(max(0.0, start), total_duration)
            end = min(max(start + 0.18, end), total_duration)
        else:
            start = max(0.0, start)
            end = max(start + 0.18, end)

        raw_segments.append({
            "text": text,
            "start": start,
            "duration": max(0.18, end - start),
        })
        last_end = end

    return raw_segments


def _fetch_youtube_transcript_with_openrouter_audio(video_id: str,
                                                    preferred_lang: str = "en") -> dict:
    if yt_dlp is None:
        raise RuntimeError("Dependência 'yt-dlp' não instalada para fallback OpenRouter.")
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY não configurada para fallback OpenRouter.")

    with tempfile.TemporaryDirectory(prefix="yt_or_audio_") as tmp:
        tmp_dir = Path(tmp)
        outtmpl = str(tmp_dir / "%(id)s.%(ext)s")
        url = f"https://www.youtube.com/watch?v={video_id}"
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio[abr<=64]/worstaudio/worst",
            "outtmpl": outtmpl,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = _find_downloaded_audio_file(tmp_dir, info, ydl)
        total_duration = float(info.get("duration", 0.0) or 0.0)

        if not audio_path or not audio_path.exists():
            raise ValueError("Não foi possível baixar o áudio para fallback OpenRouter.")

        file_bytes = audio_path.read_bytes()
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > 10.0:
            raise ValueError(
                "Áudio muito grande para fallback OpenRouter (>10MB). "
                "Use vídeo menor ou configure OPENAI_API_KEY."
            )

        audio_b64 = base64.b64encode(file_bytes).decode("ascii")
        audio_format = audio_path.suffix.lstrip(".").lower() or "webm"

    system_prompt = (
        "Você é um motor de transcrição para karaoke. "
        "Retorne APENAS JSON válido sem markdown no formato: "
        '{"language":"<iso>",'
        '"first_vocal_start_sec":0.0,'
        '"segments":[{"start":0.0,"end":1.2,"text":"..."}]}. '
        "Cada segmento deve ter ~1 a 4 segundos, em ordem cronológica, "
        "com timestamps ABSOLUTOS coerentes com o áudio (timeline inicia em 0 no vídeo). "
        "Se houver intro instrumental, reflita isso em first_vocal_start_sec e no start do primeiro segmento."
    )
    user_prompt = (
        "Transcreva o áudio no idioma original com timestamps para karaoke. "
        "Não resuma, não traduza. "
        f"Idioma preferido: {preferred_lang or 'en'}. "
        "Retorne somente JSON."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Shadowing Practice for Fluency",
    }
    payload = {
        "model": OPENROUTER_AUDIO_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": audio_format,
                        },
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 8000,
    }

    resp = http_requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=240)
    if resp.status_code != 200:
        raise RuntimeError(
            "Falha no OpenRouter áudio: "
            f"{resp.status_code} {resp.text[:220]}"
        )

    data = resp.json()
    message_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(message_content, list):
        message_content = "".join(
            c.get("text", "") if isinstance(c, dict) else str(c)
            for c in message_content
        )
    message_content = str(message_content or "").strip()

    parsed = _extract_json_payload_from_text(message_content) or {}
    raw_segments = _model_payload_to_timed_segments(parsed, total_duration)
    used_timed_output = bool(raw_segments)
    timing_offset_sec = 0.0

    model_first_vocal = _coerce_float(
        parsed.get("first_vocal_start_sec")
        or parsed.get("first_vocal_start")
        or parsed.get("vocal_start_sec")
        or parsed.get("intro_offset_sec")
    )

    # Salvage: if model returned malformed JSON, recover per-segment objects.
    if not raw_segments and "start" in message_content and "text" in message_content:
        recovered_items = _extract_segment_dicts_from_text(message_content)
        if recovered_items:
            raw_segments = _model_payload_to_timed_segments(
                {"segments": recovered_items},
                total_duration,
            )
            used_timed_output = bool(raw_segments)

    if not raw_segments:
        transcript_text = _clean_caption_text(parsed.get("text", "") or message_content)
        if not transcript_text:
            raise ValueError("Fallback OpenRouter retornou transcrição vazia.")
        raw_segments = _text_to_timed_segments(transcript_text, total_duration)
        used_timed_output = False

    # Auto-align: some models return relative timeline (voice starts at 0)
    # even when the video has an instrumental intro.
    if raw_segments and used_timed_output:
        first_start = min(seg.get("start", 0.0) for seg in raw_segments)
        detected_vocal = model_first_vocal

        if (
            detected_vocal is None
            and first_start <= 1.5
            and total_duration > 30
        ):
            detected_vocal = _estimate_first_vocal_start_openrouter(
                audio_b64, audio_format, total_duration
            )

        if detected_vocal is not None:
            detected_vocal = min(max(0.0, detected_vocal), total_duration or detected_vocal)
            shift = detected_vocal - first_start
            if shift >= 1.5:
                raw_segments = _shift_raw_segments(raw_segments, shift, total_duration)
                timing_offset_sec = round(shift, 3)

    segments = _normalize_transcript_segments(raw_segments)
    if used_timed_output:
        # Preserve line granularity and timing fidelity when model returns timestamps.
        segments = sorted(segments, key=lambda s: s["start"])
    else:
        segments = _merge_transcript_segments(segments)
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.24, max_chars=220, max_duration=20.0
    )
    if not segments:
        raise ValueError("Falha ao construir segmentos do fallback OpenRouter.")

    # Guardrail: very short transcription usually means model truncated/refused lyrics.
    transcript_words = sum(len(seg["text"].split()) for seg in segments)
    if total_duration > 30 and (transcript_words < 10 or len(segments) < 3):
        raise ValueError(
            "Transcrição do OpenRouter veio curta demais para karaoke "
            "(provável truncamento do modelo)."
        )

    language = parsed.get("language") or preferred_lang or ""
    word_count = transcript_words
    total_seg_duration = max(seg["end"] for seg in segments)
    return {
        "segments": segments,
        "language_code": language,
        "language": language,
        "is_generated": True,
        "source": "openrouter_audio_timed" if used_timed_output else "openrouter_audio",
        "timing_offset_sec": timing_offset_sec,
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_seg_duration, 2),
        },
    }


def _find_downloaded_audio_file(tmp_dir: Path, info: dict, ydl) -> Path | None:
    expected = Path(ydl.prepare_filename(info))
    if expected.exists():
        return expected

    # Alguns formatos podem ajustar extensão após download
    candidates = sorted(
        [p for p in tmp_dir.glob("*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _get_local_whisper_model():
    global _LOCAL_WHISPER_MODEL_CACHE
    if WhisperModel is None:
        raise RuntimeError("Dependência 'faster-whisper' não instalada.")

    if _LOCAL_WHISPER_MODEL_CACHE is None:
        _LOCAL_WHISPER_MODEL_CACHE = WhisperModel(
            LOCAL_WHISPER_MODEL,
            device=LOCAL_WHISPER_DEVICE,
            compute_type=LOCAL_WHISPER_COMPUTE_TYPE,
        )
    return _LOCAL_WHISPER_MODEL_CACHE


def _fetch_youtube_transcript_with_local_whisper(video_id: str,
                                                 preferred_lang: str = "en") -> dict:
    if yt_dlp is None:
        raise RuntimeError("Dependência 'yt-dlp' não instalada para fallback local.")
    if WhisperModel is None:
        raise RuntimeError("Dependência 'faster-whisper' não instalada.")

    with tempfile.TemporaryDirectory(prefix="yt_local_whisper_") as tmp:
        tmp_dir = Path(tmp)
        outtmpl = str(tmp_dir / "%(id)s.%(ext)s")
        url = f"https://www.youtube.com/watch?v={video_id}"
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio[abr<=64]/worstaudio/worst",
            "outtmpl": outtmpl,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = _find_downloaded_audio_file(tmp_dir, info, ydl)
        total_duration = float(info.get("duration", 0.0) or 0.0)

        if not audio_path or not audio_path.exists():
            raise ValueError("Não foi possível baixar o áudio para whisper local.")

        model = _get_local_whisper_model()
        lang = (preferred_lang or "").strip().lower().split("-")[0]
        language = lang if len(lang) == 2 else None

        seg_iter, transcribe_info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            best_of=5,
            vad_filter=False,
            condition_on_previous_text=True,
        )

        raw_segments = []
        for seg in seg_iter:
            text = _clean_caption_text(seg.text or "")
            if not text:
                continue
            start = float(seg.start or 0.0)
            end = float(seg.end or (start + 0.8))
            if end <= start:
                end = start + 0.18
            raw_segments.append({
                "text": text,
                "start": start,
                "duration": max(0.18, end - start),
            })

        timing_offset_sec = 0.0
        if raw_segments and OPENROUTER_API_KEY and total_duration > 30:
            first_start = min(seg.get("start", 0.0) for seg in raw_segments)
            if first_start <= 1.5:
                try:
                    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")
                    audio_format = audio_path.suffix.lstrip(".").lower() or "webm"
                    detected_vocal = _estimate_first_vocal_start_openrouter(
                        audio_b64, audio_format, total_duration
                    )
                except Exception:
                    detected_vocal = None

                if detected_vocal is not None:
                    shift = float(detected_vocal) - float(first_start)
                    if shift >= 1.5:
                        raw_segments = _shift_raw_segments(raw_segments, shift, total_duration)
                        timing_offset_sec = round(shift, 3)

    segments = _normalize_transcript_segments(raw_segments)
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.24, max_chars=220, max_duration=20.0
    )
    if not segments:
        raise ValueError("Whisper local não retornou segmentos válidos.")

    word_count = sum(len(seg["text"].split()) for seg in segments)
    total_seg_duration = max(seg["end"] for seg in segments)
    lang_code = getattr(transcribe_info, "language", "") or preferred_lang or ""
    return {
        "segments": segments,
        "language_code": lang_code,
        "language": lang_code,
        "is_generated": True,
        "source": "local_whisper",
        "timing_offset_sec": timing_offset_sec,
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_seg_duration, 2),
        },
    }


def _openai_transcribe_audio_file(file_path: Path, preferred_lang: str = "en") -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY não configurada para fallback de áudio.")

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    language = (preferred_lang or "").strip().lower().split("-")[0]

    data = [
        ("model", "whisper-1"),
        ("response_format", "verbose_json"),
        ("temperature", "0"),
        ("timestamp_granularities[]", "segment"),
    ]
    if language:
        data.append(("language", language))

    with file_path.open("rb") as audio_file:
        files = {
            "file": (file_path.name, audio_file, "application/octet-stream"),
        }
        resp = http_requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            data=data,
            files=files,
            timeout=300,
        )

    if resp.status_code != 200:
        raise RuntimeError(
            "Falha no OpenAI transcription: "
            f"{resp.status_code} {resp.text[:220]}"
        )
    return resp.json()


def _fetch_youtube_transcript_with_openai(video_id: str, preferred_lang: str = "en") -> dict:
    if yt_dlp is None:
        raise RuntimeError("Dependência 'yt-dlp' não instalada no ambiente.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY não configurada para transcrição por áudio.")

    with tempfile.TemporaryDirectory(prefix="yt_audio_") as tmp:
        tmp_dir = Path(tmp)
        outtmpl = str(tmp_dir / "%(id)s.%(ext)s")
        url = f"https://www.youtube.com/watch?v={video_id}"

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio[abr<=64]/worstaudio/worst",
            "outtmpl": outtmpl,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = _find_downloaded_audio_file(tmp_dir, info, ydl)

        if not audio_path or not audio_path.exists():
            raise ValueError("Não foi possível baixar o áudio do vídeo para transcrição.")

        size_mb = audio_path.stat().st_size / (1024 * 1024)
        if size_mb > 24.0:
            raise ValueError(
                "Áudio muito grande para transcrição automática (>24MB). "
                "Use vídeo menor ou com legendas ativas."
            )

        transcription = _openai_transcribe_audio_file(audio_path, preferred_lang)

    raw_segments = []
    for seg in transcription.get("segments", []) or []:
        text = _clean_caption_text(seg.get("text", ""))
        if not text:
            continue
        start = float(seg.get("start", 0.0) or 0.0)
        end = float(seg.get("end", start + 1.0) or (start + 1.0))
        raw_segments.append({
            "text": text,
            "start": start,
            "duration": max(0.18, end - start),
        })

    if not raw_segments and transcription.get("text"):
        text = _clean_caption_text(transcription["text"])
        if text:
            duration = float(transcription.get("duration", 8.0) or 8.0)
            raw_segments = [{
                "text": text,
                "start": 0.0,
                "duration": max(0.18, duration),
            }]

    segments = _normalize_transcript_segments(raw_segments)
    segments = _merge_sentence_like_segments(
        segments, max_gap=0.24, max_chars=220, max_duration=20.0
    )
    if not segments:
        raise ValueError("Transcrição por áudio retornou conteúdo vazio.")

    word_count = sum(len(seg["text"].split()) for seg in segments)
    total_duration = max(seg["end"] for seg in segments)
    language = transcription.get("language") or (preferred_lang or "")
    return {
        "segments": segments,
        "language_code": language,
        "language": language,
        "is_generated": True,
        "source": "openai_whisper",
        "stats": {
            "segments": len(segments),
            "words": word_count,
            "duration_sec": round(total_duration, 2),
        },
    }


# ──────────────────────────────────────────────────────────────
# LMNT — Voz Natural
# ──────────────────────────────────────────────────────────────
def _piper_model_and_config_for_lang(lang: str) -> tuple[Path | None, Path | None]:
    model_path = PIPER_MODEL_PATHS.get(lang)
    if model_path is None:
        return None, None
    config_path = Path(f"{model_path}.json")
    return model_path, config_path


def piper_supported_languages() -> list[str]:
    if not PIPER_ENABLED:
        return []
    supported = []
    for lang, model_path in PIPER_MODEL_PATHS.items():
        config_path = Path(f"{model_path}.json")
        if model_path.exists() and config_path.exists():
            supported.append(lang)
    return supported


def piper_local_models() -> list[dict[str, Any]]:
    if not PIPER_ENABLED:
        return []
    models = []
    for lang, model_path in PIPER_MODEL_PATHS.items():
        config_path = Path(f"{model_path}.json")
        if not model_path.exists() or not config_path.exists():
            continue
        voice_override = _resolve_piper_voice_override(model_path, lang)
        models.append({
            "lang": lang,
            "label": voice_override.get("label") or model_path.stem,
            "model_id": model_path.stem,
            "model_path": str(model_path),
            "config_path": str(config_path),
            "voice_tuning": {
                "label": voice_override.get("label", ""),
                "key": voice_override.get("key", ""),
                "notes": voice_override.get("notes", ""),
            } if voice_override else {},
        })
    return models


def piper_available(lang: str | None = None) -> bool:
    if not PIPER_ENABLED:
        return False
    if lang:
        model_path, config_path = _piper_model_and_config_for_lang(lang)
        return bool(model_path and config_path and model_path.exists() and config_path.exists())
    return bool(piper_supported_languages())


def _clamp_float_option(
    value,
    *,
    default: float,
    min_value: float,
    max_value: float,
) -> float:
    coerced = _coerce_float(value)
    if coerced is None:
        coerced = default
    return max(min_value, min(max_value, float(coerced)))


def _normalize_piper_profile(value, default: str = "auto") -> str:
    raw = str(value or default).strip().lower().replace("-", "_")
    aliases = {
        "auto": "auto",
        "default": "balanced",
        "general": "balanced",
        "balanced": "balanced",
        "dialogue": "chat",
        "dialog": "chat",
        "conversation": "chat",
        "conversational": "chat",
        "chat": "chat",
        "lesson": "lesson",
        "teacher": "lesson",
        "didactic": "lesson",
        "didatico": "lesson",
        "teaching": "lesson",
        "correction": "lesson",
        "story": "story",
        "narration": "story",
        "narrative": "story",
        "question": "question",
        "expressive": "expressive",
        "energetic": "expressive",
        "emphatic": "expressive",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in {"auto", *PIPER_PROFILE_ADJUSTMENTS.keys()} else default


def _extract_piper_request_options(data: dict | None = None) -> dict[str, Any]:
    payload = data if isinstance(data, dict) else {}
    nested = payload.get("piper_options")
    nested = nested if isinstance(nested, dict) else {}

    def first_present(*values):
        for item in values:
            if item is None:
                continue
            if isinstance(item, str) and not item.strip():
                continue
            return item
        return None

    speaker_value = first_present(
        nested.get("speaker_id"),
        nested.get("piper_speaker_id"),
        payload.get("piper_speaker_id"),
        payload.get("speaker_id"),
    )
    speaker_id = None
    if speaker_value not in {None, ""}:
        speaker_id = _coerce_int(
            speaker_value,
            default=0,
            min_value=0,
            max_value=2048,
        )

    options: dict[str, Any] = {
        "profile": _normalize_piper_profile(
            first_present(
                nested.get("profile"),
                nested.get("style"),
                payload.get("piper_profile"),
                payload.get("tts_style"),
                payload.get("style"),
            ),
            default="auto",
        ),
        "context_hint": str(
            first_present(
                nested.get("context_hint"),
                payload.get("tts_context"),
                payload.get("context_hint"),
                payload.get("text_type"),
                payload.get("practice_type"),
            )
            or ""
        ).strip(),
    }
    if speaker_id is not None:
        options["speaker_id"] = speaker_id

    apply_lexicon = first_present(
        nested.get("apply_lexicon"),
        payload.get("apply_lexicon"),
        payload.get("apply_pronunciation_lexicon"),
    )
    if apply_lexicon is not None:
        options["apply_lexicon"] = _coerce_bool(apply_lexicon, default=True)

    normalize_text = first_present(
        nested.get("normalize_text"),
        payload.get("normalize_tts_text"),
        payload.get("normalize_text"),
    )
    if normalize_text is not None:
        options["normalize_text"] = _coerce_bool(normalize_text, default=True)

    normalize_audio = first_present(
        nested.get("normalize_audio"),
        payload.get("normalize_audio"),
    )
    if normalize_audio is not None:
        options["normalize_audio"] = _coerce_bool(normalize_audio, default=True)

    numeric_fields = (
        "length_scale",
        "noise_scale",
        "noise_w_scale",
        "sentence_silence",
        "volume",
    )
    for field in numeric_fields:
        value = first_present(nested.get(field), payload.get(field))
        if value is not None:
            options[field] = value

    model_path = first_present(
        nested.get("model_path"),
        payload.get("piper_model_path"),
        payload.get("model_path"),
    )
    if model_path is not None:
        options["model_path"] = str(model_path).strip()

    config_path = first_present(
        nested.get("config_path"),
        payload.get("piper_config_path"),
        payload.get("config_path"),
    )
    if config_path is not None:
        options["config_path"] = str(config_path).strip()

    postprocess_filter = first_present(
        nested.get("postprocess_filter"),
        payload.get("piper_postprocess_filter"),
        payload.get("postprocess_filter"),
    )
    if postprocess_filter is not None:
        options["postprocess_filter"] = str(postprocess_filter).strip()

    return options


def _build_piper_request_options(
    data: dict | None = None,
    *,
    default_context_hint: str = "",
    default_profile: str = "auto",
) -> dict[str, Any]:
    options = _extract_piper_request_options(data)
    if default_context_hint and not options.get("context_hint"):
        options["context_hint"] = default_context_hint
    if options.get("profile") in {None, "", "auto"}:
        chosen_profile = _normalize_piper_profile(default_profile, default="auto")
        if chosen_profile == "auto":
            context_hint = str(options.get("context_hint") or "").strip().lower().replace("-", "_")
            chosen_profile = PIPER_DEFAULT_PROFILE_BY_CONTEXT.get(context_hint, "auto")
        if chosen_profile != "auto":
            options["profile"] = chosen_profile
    return options


def _looks_like_question(text: str, lang: str = "en") -> bool:
    normalized = re.sub(r"\s+", " ", str(text or "").strip().lower())
    if not normalized:
        return False
    if "?" in normalized:
        return True
    if normalized.endswith(" right") or normalized.endswith(" não é"):
        return True
    prefixes = PIPER_QUESTION_PREFIXES.get(
        _normalize_lang(lang, default="en"),
        PIPER_QUESTION_PREFIXES.get("en", ()),
    )
    return normalized.startswith(prefixes)


def _infer_piper_profile(text: str, lang: str = "en", context_hint: str = "") -> str:
    hint = str(context_hint or "").strip().lower().replace("-", "_")
    if hint:
        if any(token in hint for token in ("chat", "dialog", "conversation", "reply")):
            return "chat"
        if any(token in hint for token in ("lesson", "teach", "correction", "feedback", "analysis")):
            return "lesson"
        if any(token in hint for token in ("story", "narrat", "karaoke", "youtube")):
            return "story"
        if "question" in hint:
            return "question"
        if any(token in hint for token in ("expressive", "energy", "excited")):
            return "expressive"

    if re.findall(r"(?m)^\s*[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,24}:\s*", text or ""):
        return "chat"
    if _looks_like_question(text, lang):
        return "question"
    if "!" in str(text or ""):
        return "expressive"
    return "balanced"


def _load_piper_pronunciation_lexicon() -> dict[str, list[dict[str, Any]]]:
    path = PIPER_LEXICON_PATH
    cache_key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}

    cache = getattr(_load_piper_pronunciation_lexicon, "_cache", None)
    if (
        isinstance(cache, dict)
        and cache.get("path") == cache_key
        and cache.get("mtime") == mtime
    ):
        return cache.get("entries", {})

    entries: dict[str, list[dict[str, Any]]] = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[Piper] Não foi possível ler léxico de pronúncia: {exc}")
        payload = {}

    if isinstance(payload, dict):
        for raw_lang, raw_items in payload.items():
            lang_key = str(raw_lang or "").strip().lower()
            if not lang_key or lang_key.startswith("_") or not isinstance(raw_items, list):
                continue
            if lang_key in {"global", "*", "default"}:
                normalized_lang = "global"
            else:
                normalized_lang = _normalize_lang(lang_key, default=lang_key)

            cleaned_items = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                match_text = str(item.get("match") or "").strip()
                replacement_text = str(
                    item.get("text") or item.get("replace") or ""
                ).strip()
                phonemes = str(item.get("phonemes") or "").strip()
                if not match_text or not (replacement_text or phonemes):
                    continue
                cleaned_items.append({
                    "match": match_text,
                    "replacement_text": replacement_text,
                    "phonemes": phonemes,
                    "ignore_case": _coerce_bool(item.get("ignore_case", True), default=True),
                    "word_boundary": _coerce_bool(item.get("word_boundary", True), default=True),
                })
            if cleaned_items:
                entries.setdefault(normalized_lang, []).extend(cleaned_items)

    _load_piper_pronunciation_lexicon._cache = {
        "path": cache_key,
        "mtime": mtime,
        "entries": entries,
    }
    return entries


def _load_piper_voice_overrides() -> dict[str, dict[str, Any]]:
    path = PIPER_VOICE_OVERRIDES_PATH
    cache_key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}

    cache = getattr(_load_piper_voice_overrides, "_cache", None)
    if (
        isinstance(cache, dict)
        and cache.get("path") == cache_key
        and cache.get("mtime") == mtime
    ):
        return cache.get("entries", {})

    normalized_entries: dict[str, dict[str, Any]] = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[Piper] Não foi possível ler tuning por voz: {exc}")
        payload = {}

    model_items = payload.get("models") if isinstance(payload, dict) else {}
    if not isinstance(model_items, dict):
        model_items = {}

    for raw_key, raw_item in model_items.items():
        if not isinstance(raw_item, dict):
            continue
        key = str(raw_key or "").strip()
        if not key:
            continue
        normalized_entries[key] = raw_item
        normalized_entries.setdefault(Path(key).name, raw_item)
        normalized_entries.setdefault(Path(key).stem, raw_item)

    _load_piper_voice_overrides._cache = {
        "path": cache_key,
        "mtime": mtime,
        "entries": normalized_entries,
    }
    return normalized_entries


def _resolve_piper_voice_override(
    model_path: Path | str | None,
    lang: str = "en",
) -> dict[str, Any]:
    if not model_path:
        return {}

    path_obj = Path(model_path)
    lookup = _load_piper_voice_overrides()
    candidates = []
    try:
        candidates.append(str(path_obj.resolve()))
    except OSError:
        pass
    candidates.extend([
        str(path_obj),
        path_obj.name,
        path_obj.stem,
    ])
    try:
        candidates.append(str(path_obj.resolve().relative_to(BASE_DIR.resolve())))
    except Exception:
        pass

    for key in candidates:
        if key in lookup:
            item = lookup[key]
            return {
                "key": key,
                "label": str(item.get("label") or path_obj.stem),
                "lang": _normalize_lang(item.get("lang"), default=lang),
                "base": item.get("base", {}) if isinstance(item.get("base"), dict) else {},
                "profiles": item.get("profiles", {}) if isinstance(item.get("profiles"), dict) else {},
                "postprocess_filter": str(item.get("postprocess_filter") or "").strip(),
                "postprocess_filters": (
                    item.get("postprocess_filters")
                    if isinstance(item.get("postprocess_filters"), dict)
                    else {}
                ),
                "notes": item.get("notes", ""),
            }
    return {}


def _apply_piper_pronunciation_lexicon(
    text: str,
    lang: str = "en",
) -> tuple[str, list[dict[str, Any]]]:
    lexicon = _load_piper_pronunciation_lexicon()
    lang_key = _normalize_lang(lang, default="en")
    entries = list(lexicon.get("global", [])) + list(lexicon.get(lang_key, []))
    if not entries:
        return text, []

    working = text
    applied = []
    ordered_entries = sorted(entries, key=lambda item: len(item["match"]), reverse=True)
    for item in ordered_entries:
        flags = re.IGNORECASE if item.get("ignore_case", True) else 0
        escaped = re.escape(item["match"])
        if item.get("word_boundary", True):
            pattern = rf"(?<!\w){escaped}(?!\w)"
        else:
            pattern = escaped
        replacement = (
            f"[[ {item['phonemes']} ]]"
            if item.get("phonemes")
            else item["replacement_text"]
        )
        working, count = re.subn(pattern, replacement, working, flags=flags)
        if count:
            applied.append({
                "match": item["match"],
                "replacement": replacement,
                "count": count,
            })
    return working, applied


def _prepare_text_for_piper(
    text: str,
    *,
    lang: str = "en",
    profile: str = "balanced",
    context_hint: str = "",
    apply_lexicon: bool = True,
    normalize_text: bool = True,
) -> dict[str, Any]:
    working = html.unescape(str(text or ""))[:MAX_TEXT_CHARS]
    transformations: list[str] = []

    if normalize_text:
        original = working
        working = working.replace("\\n", "\n").replace("\\t", " ")
        working = working.replace("\r\n", "\n").replace("\r", "\n")
        working = _strip_emojis(working)
        working = re.sub(r"`([^`]+)`", r"\1", working)
        working = re.sub(r"\*\*([^*]+)\*\*", r"\1", working)
        working = re.sub(r"https?://\S+", "", working)
        working = re.sub(r"\s*[—–]+\s*", ", ", working)
        working = re.sub(r"[•●▪◦]", "\n", working)
        if working != original:
            transformations.append("text_normalized")

        speaker_labels = re.findall(
            r"(?m)^\s*[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,24}:\s*",
            working,
        )
        if speaker_labels and (
            len(speaker_labels) >= 2
            or "dialog" in context_hint.lower()
            or "chat" in context_hint.lower()
            or "conversation" in context_hint.lower()
        ):
            working = re.sub(
                r"(?m)^\s*[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]{0,24}:\s*",
                "",
                working,
            )
            transformations.append("speaker_labels_removed")

        lines = []
        for raw_line in working.splitlines():
            line = re.sub(r"^\s*(?:[-*]+|\d+[.)])\s+", "", raw_line.strip())
            if line:
                lines.append(line)
        if len(lines) > 1:
            normalized_lines = []
            for line in lines:
                line = re.sub(r"\s+", " ", line).strip()
                if not re.search(r"[.!?…]$", line):
                    if _looks_like_question(line, lang):
                        line += "?"
                    else:
                        line += "."
                normalized_lines.append(line)
            joiner = " " if profile == "chat" else " "
            working = joiner.join(normalized_lines)
            transformations.append("multi_line_joined")
        else:
            working = " ".join(lines) if lines else working

        working = re.sub(r"\s+([,.;!?…])", r"\1", working)
        working = re.sub(r"([,.;!?…])(?![\s\"'])", r"\1 ", working)
        working = re.sub(r"\s+", " ", working).strip()

    if working and not re.search(r"[.!?…]$", working):
        if profile == "question" or _looks_like_question(working, lang):
            working += "?"
        elif profile == "expressive":
            working += "!"
        else:
            working += "."
        transformations.append("terminal_punctuation_added")

    lexicon_matches: list[dict[str, Any]] = []
    if apply_lexicon and working:
        working, lexicon_matches = _apply_piper_pronunciation_lexicon(working, lang)
        if lexicon_matches:
            transformations.append("pronunciation_lexicon_applied")

    return {
        "prepared_text": working.strip(),
        "transformations": transformations,
        "lexicon_matches": lexicon_matches,
    }


def _build_piper_settings(
    text: str,
    *,
    lang: str = "en",
    profile: str = "balanced",
    model_path: Path | str | None = None,
    request_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = dict(PIPER_PROSODY_BASE_BY_LANG.get(lang, PIPER_PROSODY_BASE_BY_LANG["default"]))
    adjustments = PIPER_PROFILE_ADJUSTMENTS.get(profile, {})
    voice_override = _resolve_piper_voice_override(model_path, lang)
    voice_base = voice_override.get("base", {})
    settings = dict(base)
    for key, value in voice_base.items():
        if isinstance(value, (int, float, bool)):
            settings[key] = value
    for key, delta in adjustments.items():
        if isinstance(delta, bool):
            settings[key] = delta
        else:
            settings[key] = float(settings.get(key, 0.0)) + float(delta)
    voice_profile_adjustments = voice_override.get("profiles", {}).get(profile, {})
    if isinstance(voice_profile_adjustments, dict):
        for key, delta in voice_profile_adjustments.items():
            if isinstance(delta, bool):
                settings[key] = delta
            elif key in settings:
                settings[key] = float(settings.get(key, 0.0)) + float(delta)

    word_count = len(re.findall(r"\w+", text or ""))
    sentence_count = max(1, len(re.findall(r"[.!?…]", text or "")))
    avg_words = word_count / sentence_count if sentence_count else word_count
    if avg_words >= 18:
        settings["length_scale"] += 0.03
        settings["sentence_silence"] += 0.03
    if word_count <= 10 and profile in {"chat", "question"}:
        settings["length_scale"] -= 0.02
    if "?" in str(text or ""):
        settings["noise_w_scale"] += 0.01

    options = request_options or {}
    settings["length_scale"] = _clamp_float_option(
        options.get("length_scale", settings["length_scale"]),
        default=settings["length_scale"],
        min_value=0.75,
        max_value=1.35,
    )
    settings["noise_scale"] = _clamp_float_option(
        options.get("noise_scale", settings["noise_scale"]),
        default=settings["noise_scale"],
        min_value=0.2,
        max_value=1.6,
    )
    settings["noise_w_scale"] = _clamp_float_option(
        options.get("noise_w_scale", settings["noise_w_scale"]),
        default=settings["noise_w_scale"],
        min_value=0.2,
        max_value=1.4,
    )
    settings["sentence_silence"] = _clamp_float_option(
        options.get("sentence_silence", settings["sentence_silence"]),
        default=settings["sentence_silence"],
        min_value=0.0,
        max_value=0.6,
    )
    settings["volume"] = _clamp_float_option(
        options.get("volume", settings["volume"]),
        default=settings["volume"],
        min_value=0.4,
        max_value=1.8,
    )
    settings["normalize_audio"] = _coerce_bool(
        options.get("normalize_audio", settings.get("normalize_audio", True)),
        default=True,
    )
    settings["_voice_override"] = voice_override
    return settings


def _public_piper_meta(result: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = result if isinstance(result, dict) else {}
    profile = str(payload.get("profile") or "balanced")
    return {
        "profile": profile,
        "profile_label": PIPER_PROFILE_LABELS.get(profile, profile),
        "context_hint": payload.get("context_hint", ""),
        "settings": payload.get("settings", {}),
        "transformations": payload.get("transformations", []),
        "lexicon_matches": payload.get("lexicon_matches", []),
        "speaker_id": payload.get("speaker_id"),
        "prepared_text": payload.get("prepared_text", ""),
        "model_path": payload.get("model_path", ""),
        "model_id": payload.get("model_id", ""),
        "voice_tuning": payload.get("voice_tuning", {}),
        "postprocess": payload.get("postprocess", {}),
    }


def _resolve_piper_postprocess_filter(
    *,
    request_options: dict[str, Any] | None = None,
    voice_override: dict[str, Any] | None = None,
    profile: str = "balanced",
) -> str:
    options = request_options if isinstance(request_options, dict) else {}
    voice = voice_override if isinstance(voice_override, dict) else {}

    explicit_filter = str(options.get("postprocess_filter") or "").strip()
    if explicit_filter:
        return explicit_filter

    profile_filters = voice.get("postprocess_filters", {})
    if isinstance(profile_filters, dict):
        scoped_filter = str(profile_filters.get(profile) or "").strip()
        if scoped_filter:
            return scoped_filter

    voice_filter = str(voice.get("postprocess_filter") or "").strip()
    if voice_filter:
        return voice_filter

    return PIPER_POSTPROCESS_FILTER


def _ffmpeg_bin() -> str:
    cached = getattr(_ffmpeg_bin, "_cache", None)
    if cached is not None:
        return cached
    resolved = shutil.which("ffmpeg") or ""
    _ffmpeg_bin._cache = resolved
    return resolved


def _postprocess_piper_audio(output_path: Path, *, filter_spec: str = "") -> dict[str, Any]:
    if not PIPER_POSTPROCESS_ENABLED:
        return {"ok": False, "reason": "disabled"}
    effective_filter = str(filter_spec or "").strip() or PIPER_POSTPROCESS_FILTER
    if not effective_filter:
        return {"ok": False, "reason": "filter_missing"}
    ffmpeg_bin = _ffmpeg_bin()
    if not ffmpeg_bin:
        return {"ok": False, "reason": "ffmpeg_unavailable"}
    if not output_path.exists() or output_path.stat().st_size <= 0:
        return {"ok": False, "reason": "file_missing"}

    temp_path = output_path.with_name(f"{output_path.stem}.post{output_path.suffix}")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(output_path),
        "-af",
        effective_filter,
        "-ac",
        "1",
        "-ar",
        "22050",
        "-c:a",
        "pcm_s16le",
        str(temp_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PIPER_POSTPROCESS_TIMEOUT_SEC,
            check=False,
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "reason": "ffmpeg_failed",
                "error": (result.stderr or result.stdout or "").strip()[:220],
                "filter": effective_filter,
            }
        if not temp_path.exists() or temp_path.stat().st_size <= 0:
            return {
                "ok": False,
                "reason": "empty_output",
                "filter": effective_filter,
            }
        temp_path.replace(output_path)
        return {
            "ok": True,
            "filter": effective_filter,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "exception",
            "error": str(exc)[:220],
            "filter": effective_filter,
        }
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def piper_synthesize_to_file(
    text: str,
    output_path: Path,
    lang: str = "en",
    request_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Gera áudio WAV local com Piper e retorna metadados do processo."""
    meta: dict[str, Any] = {
        "ok": False,
        "engine": "piper",
        "lang": _normalize_lang(lang, default="en"),
        "profile": "balanced",
        "context_hint": "",
        "settings": {},
        "transformations": [],
        "lexicon_matches": [],
    }
    if not PIPER_ENABLED:
        meta["error"] = "Piper desativado."
        return meta

    lang = meta["lang"]
    options = request_options if isinstance(request_options, dict) else {}
    custom_model_path = str(options.get("model_path") or "").strip()
    custom_config_path = str(options.get("config_path") or "").strip()
    if custom_model_path:
        model_path = Path(custom_model_path)
        config_path = Path(custom_config_path) if custom_config_path else Path(f"{model_path}.json")
    else:
        model_path, config_path = _piper_model_and_config_for_lang(lang)
    if not model_path or not config_path or not model_path.exists() or not config_path.exists():
        print(
            "[Piper] Modelo ausente. "
            f"lang={lang} model={model_path} config={config_path}"
        )
        meta["error"] = "Modelo Piper ausente."
        return meta

    context_hint = str(options.get("context_hint") or "").strip()
    profile = _normalize_piper_profile(options.get("profile"), default="auto")
    selected_profile = (
        _infer_piper_profile(text, lang, context_hint)
        if profile == "auto"
        else profile
    )
    prepared = _prepare_text_for_piper(
        text,
        lang=lang,
        profile=selected_profile,
        context_hint=context_hint,
        apply_lexicon=_coerce_bool(
            options.get("apply_lexicon", PIPER_CONTEXTUAL_ENABLED),
            default=PIPER_CONTEXTUAL_ENABLED,
        ),
        normalize_text=_coerce_bool(
            options.get("normalize_text", PIPER_CONTEXTUAL_ENABLED),
            default=PIPER_CONTEXTUAL_ENABLED,
        ),
    )
    prepared_text = prepared.get("prepared_text", "").strip()
    if not prepared_text:
        meta["error"] = "Texto vazio após normalização do Piper."
        return meta

    settings = _build_piper_settings(
        prepared_text,
        lang=lang,
        profile=selected_profile,
        model_path=model_path,
        request_options=options,
    )
    voice_override = settings.pop("_voice_override", {}) if isinstance(settings, dict) else {}
    postprocess_filter = _resolve_piper_postprocess_filter(
        request_options=options,
        voice_override=voice_override,
        profile=selected_profile,
    )

    speaker_id = _coerce_int(
        options.get("speaker_id", os.getenv("PIPER_SPEAKER", "0")),
        default=0,
        min_value=0,
        max_value=2048,
    )
    cmd = [
        sys.executable,
        "-m",
        "piper",
        "-m",
        str(model_path),
        "-c",
        str(config_path),
        "-f",
        str(output_path),
        "-s",
        str(speaker_id),
        "--length-scale",
        f"{settings['length_scale']:.3f}",
        "--noise-scale",
        f"{settings['noise_scale']:.3f}",
        "--noise-w-scale",
        f"{settings['noise_w_scale']:.3f}",
        "--sentence-silence",
        f"{settings['sentence_silence']:.3f}",
        "--volume",
        f"{settings['volume']:.3f}",
    ]
    if not settings.get("normalize_audio", True):
        cmd.append("--no-normalize")

    meta.update({
        "profile": selected_profile,
        "context_hint": context_hint,
        "settings": settings,
        "transformations": prepared.get("transformations", []),
        "lexicon_matches": prepared.get("lexicon_matches", []),
        "speaker_id": speaker_id,
        "prepared_text": prepared_text,
        "model_path": str(model_path),
        "config_path": str(config_path),
        "model_id": model_path.stem,
        "voice_tuning": {
                "label": voice_override.get("label", ""),
                "key": voice_override.get("key", ""),
                "notes": voice_override.get("notes", ""),
                "postprocess_filter": postprocess_filter,
            } if voice_override else {},
    })

    try:
        result = subprocess.run(
            cmd,
            input=prepared_text[:5000],
            text=True,
            capture_output=True,
            timeout=PIPER_TIMEOUT_SEC,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"[Piper] Erro (exit={result.returncode}): "
                f"{(result.stderr or result.stdout or '').strip()[:220]}"
            )
            meta["error"] = (result.stderr or result.stdout or "").strip()[:220]
            return meta
        meta["ok"] = output_path.exists() and output_path.stat().st_size > 0
        if not meta["ok"]:
            meta["error"] = "Piper não gerou arquivo de áudio."
            return meta
        postprocess = _postprocess_piper_audio(output_path, filter_spec=postprocess_filter)
        meta["postprocess"] = postprocess
        if postprocess.get("ok"):
            meta["transformations"] = [
                *meta.get("transformations", []),
                "audio_postprocessed",
            ]
        return meta
    except Exception as exc:
        print(f"[Piper] Exceção: {exc}")
        meta["error"] = str(exc)
        return meta


def _deepgram_tts_model_for_lang(lang: str) -> str:
    if DEEPGRAM_TTS_MODEL:
        return DEEPGRAM_TTS_MODEL
    normalized = str(lang or "").strip().lower().split("-")[0]
    return DEEPGRAM_TTS_MODELS_BY_LANG.get(normalized, "")


def deepgram_tts_supported_languages() -> list[str]:
    return sorted(DEEPGRAM_TTS_MODELS_BY_LANG.keys())


def deepgram_synthesize(text: str, lang: str = "en") -> bytes | None:
    """Gera áudio com Deepgram Aura-2 (Speak API). Retorna bytes MP3 ou None."""
    if not (DEEPGRAM_ENABLED and DEEPGRAM_API_KEY):
        return None

    model = _deepgram_tts_model_for_lang(lang)
    if not model:
        print(f"[Deepgram TTS] Sem modelo para idioma '{lang}'.")
        return None

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    params = {
        "model": model,
        "encoding": "mp3",
    }
    payload = {"text": text[:5000]}

    try:
        resp = http_requests.post(
            DEEPGRAM_SPEAK_URL,
            headers=headers,
            params=params,
            json=payload,
            timeout=DEEPGRAM_TTS_TIMEOUT_SEC,
        )
        if resp.status_code == 200 and resp.content:
            return resp.content
        print(f"[Deepgram TTS] Erro {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as exc:
        print(f"[Deepgram TTS] Exceção: {exc}")
        return None


def lmnt_synthesize(text: str, voice: str = "leah", lang: str = "en") -> bytes | None:
    """Gera áudio com voz natural via LMNT (sem durations). Retorna bytes MP3 ou None."""
    if not LMNT_API_KEY:
        return None

    valid_langs = ("auto", "ar", "de", "en", "es", "fr", "hi", "id", "it",
                   "ja", "ko", "nl", "pl", "pt", "ru", "sv", "th", "tr",
                   "uk", "ur", "vi", "zh")

    payload = {
        "text": text[:5000],
        "voice": voice,
        "language": lang if lang in valid_langs else "auto",
        "format": "mp3",
        "model": "blizzard",
    }
    headers = {
        "X-API-Key": LMNT_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        resp = http_requests.post(LMNT_SPEECH_URL, json=payload,
                                  headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.content
        print(f"[LMNT] Erro {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as exc:
        print(f"[LMNT] Exceção: {exc}")
        return None


def lmnt_synthesize_with_durations(text: str, voice: str = "leah",
                                   lang: str = "en") -> tuple[bytes | None, list | None]:
    """Gera áudio via LMNT com word-level durations para sincronização.
    Retorna (audio_bytes, durations_list) ou (None, None)."""
    if not LMNT_API_KEY:
        return None, None

    valid_langs = ("auto", "ar", "de", "en", "es", "fr", "hi", "id", "it",
                   "ja", "ko", "nl", "pl", "pt", "ru", "sv", "th", "tr",
                   "uk", "ur", "vi", "zh")

    payload = {
        "text": text[:5000],
        "voice": voice,
        "language": lang if lang in valid_langs else "auto",
        "format": "mp3",
        "model": "blizzard",
        "return_durations": True,
    }
    headers = {
        "X-API-Key": LMNT_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        resp = http_requests.post(LMNT_SPEECH_DETAILED_URL, json=payload,
                                  headers=headers, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            audio_b64 = data.get("audio", "")
            audio_bytes = base64.b64decode(audio_b64) if audio_b64 else None
            durations = data.get("durations", [])
            return audio_bytes, durations
        print(f"[LMNT Detailed] Erro {resp.status_code}: {resp.text[:200]}")
        # Fallback to bytes endpoint without durations
        return lmnt_synthesize(text, voice=voice, lang=lang), None
    except Exception as exc:
        print(f"[LMNT Detailed] Exceção: {exc}")
        return lmnt_synthesize(text, voice=voice, lang=lang), None


def lmnt_list_voices() -> list:
    """Lista vozes disponíveis na LMNT."""
    if not LMNT_API_KEY:
        return []

    headers = {"X-API-Key": LMNT_API_KEY}
    try:
        resp = http_requests.get(LMNT_VOICES_URL, headers=headers,
                                 params={"owner": "all"}, timeout=15)
        if resp.status_code == 200:
            return [
                {
                    "id": v.get("id", ""),
                    "name": v.get("name", ""),
                    "gender": v.get("gender", ""),
                    "description": v.get("description", ""),
                    "owner": v.get("owner", ""),
                    "preview_url": v.get("preview_url", ""),
                }
                for v in resp.json()
                if v.get("state") == "ready"
            ]
        return []
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────
# IA textual — DeepSeek / OpenRouter / OpenAI / Ollama
# ──────────────────────────────────────────────────────────────
def openrouter_chat(system_prompt: str, user_message: str,
                    model: str = "google/gemini-2.0-flash-001",
                    max_tokens: int = 2000,
                    temperature: float = 0.7) -> str | None:
    """Chama OpenRouter e retorna a resposta da IA."""
    if not OPENROUTER_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Shadowing Practice for Fluency",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        resp = http_requests.post(OPENROUTER_URL, json=payload,
                                  headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        print(f"[OpenRouter] Erro {resp.status_code}: {resp.text[:300]}")
        return None
    except Exception as exc:
        print(f"[OpenRouter] Exceção: {exc}")
        return None


def _resolve_ollama_model(force_refresh: bool = False) -> str:
    """Resolve o modelo Ollama (env explícita ou 1º modelo local disponível)."""
    if not OLLAMA_ENABLED:
        return ""
    if OLLAMA_MODEL:
        return OLLAMA_MODEL

    now = time.time()
    cached_name = str(_OLLAMA_MODEL_CACHE.get("name") or "")
    cached_at = float(_OLLAMA_MODEL_CACHE.get("checked_at") or 0.0)

    # Evita chamadas repetidas ao /api/tags em sequência.
    if not force_refresh:
        if cached_name and (now - cached_at) < 90:
            return cached_name
        if not cached_name and (now - cached_at) < 20:
            return ""

    try:
        resp = http_requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=4)
        if resp.status_code != 200:
            print(f"[Ollama] Erro /api/tags {resp.status_code}: {resp.text[:200]}")
            _OLLAMA_MODEL_CACHE["name"] = ""
            _OLLAMA_MODEL_CACHE["checked_at"] = now
            return ""

        model_names = []
        for item in resp.json().get("models") or []:
            if not isinstance(item, dict):
                continue
            current = str(item.get("name") or item.get("model") or "").strip()
            if current:
                model_names.append(current)

        model_name = ""
        for name in model_names:
            if "embed" not in name.casefold():
                model_name = name
                break
        if not model_name and model_names:
            model_name = model_names[0]

        _OLLAMA_MODEL_CACHE["name"] = model_name
        _OLLAMA_MODEL_CACHE["checked_at"] = now
        return model_name
    except Exception as exc:
        print(f"[Ollama] Exceção ao resolver modelo: {exc}")
        _OLLAMA_MODEL_CACHE["name"] = ""
        _OLLAMA_MODEL_CACHE["checked_at"] = now
        return ""


def ollama_chat(system_prompt: str, user_message: str,
                model: str = "",
                max_tokens: int = 2000,
                temperature: float = 0.7) -> str | None:
    """Chama Ollama local e retorna a resposta da IA."""
    if not OLLAMA_ENABLED:
        return None

    candidate = str(model or "").strip()
    if not candidate or "/" in candidate:
        candidate = _resolve_ollama_model()
    if not candidate:
        return None

    payload = {
        "model": candidate,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": max(0.0, float(temperature)),
            "num_predict": max(64, int(max_tokens or 2000)),
        },
    }

    try:
        resp = http_requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SEC,
        )
        if resp.status_code != 200:
            print(f"[Ollama] Erro {resp.status_code}: {resp.text[:300]}")
            return None

        data = resp.json()
        content = _clean_caption_text((data.get("message") or {}).get("content", ""))
        if content:
            return content

        # Compat com formatos alternativos de resposta.
        fallback_content = _clean_caption_text(data.get("response", ""))
        return fallback_content or None
    except Exception as exc:
        print(f"[Ollama] Exceção: {exc}")
        return None


def has_text_ai_provider() -> bool:
    """Retorna True se houver IA textual disponível."""
    return bool(
        DEEPSEEK_API_KEY
        or OPENROUTER_API_KEY
        or OPENAI_API_KEY
        or _resolve_ollama_model()
    )


_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # geometric shapes extended
    "\U0001F800-\U0001F8FF"  # supplemental arrows
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "]+",
    flags=re.UNICODE,
)


def _strip_emojis(text: str) -> str:
    """Remove emojis e símbolos Unicode decorativos de um texto para TTS."""
    cleaned = _EMOJI_RE.sub("", text)
    # colapsa espaços múltiplos gerados pela remoção
    return re.sub(r" {2,}", " ", cleaned).strip()


def deepseek_chat(system_prompt: str, user_message: str,
                  max_tokens: int = 2000,
                  temperature: float = 0.7) -> str | None:
    """Chama DeepSeek (API compatible com OpenAI) e retorna a resposta."""
    if not DEEPSEEK_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = http_requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        print(f"[DeepSeek] Erro {resp.status_code}: {resp.text[:300]}")
        return None
    except Exception as exc:
        print(f"[DeepSeek] Exceção: {exc}")
        return None


def openai_chat(system_prompt: str, user_message: str,
                model: str = "",
                max_tokens: int = 2000,
                temperature: float = 0.7) -> str | None:
    """Chama OpenAI Chat Completions e retorna a resposta da IA."""
    if not OPENAI_API_KEY:
        return None

    candidate_model = str(model or "").strip()
    if not candidate_model or "/" in candidate_model:
        candidate_model = OPENAI_CHAT_MODEL or "gpt-4o-mini"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": candidate_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = http_requests.post(
            OPENAI_CHAT_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"[OpenAI Chat] Erro {resp.status_code}: {resp.text[:300]}")
            return None

        data = resp.json()
        message = ((data.get("choices") or [{}])[0]).get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
            joined = "\n".join(parts).strip()
            return joined or None
        return None
    except Exception as exc:
        print(f"[OpenAI Chat] Exceção: {exc}")
        return None


def chat_with_cloud_fallback(system_prompt: str, user_message: str,
                             model: str = "google/gemini-2.0-flash-001",
                             max_tokens: int = 2000,
                             temperature: float = 0.7) -> tuple[str | None, str | None]:
    """Tenta provedores cloud (DeepSeek → OpenRouter → OpenAI Chat)."""
    if DEEPSEEK_API_KEY:
        response = deepseek_chat(
            system_prompt,
            user_message,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response:
            return response, "deepseek"

    if OPENROUTER_API_KEY:
        response = openrouter_chat(
            system_prompt,
            user_message,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response:
            return response, "openrouter"

    if OPENAI_API_KEY:
        response = openai_chat(
            system_prompt,
            user_message,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if response:
            return response, "openai"

    return None, None


def chat_with_fallback(system_prompt: str, user_message: str,
                       model: str = "google/gemini-2.0-flash-001",
                       max_tokens: int = 2000,
                       temperature: float = 0.7) -> tuple[str | None, str | None]:
    """Tenta cloud primeiro; usa Ollama apenas como último recurso."""
    response, provider = chat_with_cloud_fallback(
        system_prompt,
        user_message,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if response:
        return response, provider

    response = ollama_chat(
        system_prompt,
        user_message,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if response:
        return response, "ollama"
    return None, None


def _normalize_timing_mode(value, default: str = "balanced") -> str:
    mode = str(value or default).strip().lower()
    if mode not in {"accuracy", "balanced", "fast"}:
        return default
    return mode


def _normalize_study_target_lang(value, default: str = "pt") -> str:
    raw = str(value or default).strip().lower().replace("_", "-")
    aliases = {
        "pt-br": "pt",
        "pt-pt": "pt",
        "en-us": "en",
        "en-gb": "en",
        "es-es": "es",
        "fr-fr": "fr",
        "de-de": "de",
        "it-it": "it",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in STUDY_TARGET_LANGS else default


def _normalize_lesson_focus(value, default: str = "balanced") -> str:
    raw = str(value or default).strip().lower().replace("-", "_")
    aliases = {
        "smart": "smart",
        "auto": "smart",
        "intelligent": "smart",
        "balanced": "balanced",
        "default": "balanced",
        "corrections": "corrections",
        "correction": "corrections",
        "grammar": "corrections",
        "vocabulary": "vocabulary",
        "vocab": "vocabulary",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in {"smart", "balanced", "corrections", "vocabulary"} else default


def _extract_transcript_by_mode(video_id: str,
                                preferred_lang: str,
                                timing_mode: str = "balanced") -> tuple[dict | None, list]:
    timing_mode = _normalize_timing_mode(timing_mode)
    transcript = None
    extract_errors = []
    extract_plan = []

    def _add_step(enabled: bool, fn):
        if enabled:
            extract_plan.append(fn)

    prefer_audio_first = timing_mode == "accuracy"
    prefer_caption_first = timing_mode == "fast"

    if prefer_audio_first:
        _add_step(
            DEEPGRAM_ENABLED and bool(DEEPGRAM_API_KEY),
            lambda: _fetch_youtube_transcript_with_deepgram(video_id, preferred_lang),
        )
        _add_step(
            LOCAL_WHISPER_ENABLED and WhisperModel is not None,
            lambda: _fetch_youtube_transcript_with_local_whisper(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENROUTER_API_KEY),
            lambda: _fetch_youtube_transcript_with_openrouter_audio(video_id, preferred_lang),
        )
        _add_step(
            YouTubeTranscriptApi is not None,
            lambda: _fetch_youtube_transcript(video_id, preferred_lang),
        )
        _add_step(
            yt_dlp is not None,
            lambda: _fetch_youtube_transcript_with_ytdlp(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENAI_API_KEY),
            lambda: _fetch_youtube_transcript_with_openai(video_id, preferred_lang),
        )
    elif prefer_caption_first:
        _add_step(
            YouTubeTranscriptApi is not None,
            lambda: _fetch_youtube_transcript(video_id, preferred_lang),
        )
        _add_step(
            yt_dlp is not None,
            lambda: _fetch_youtube_transcript_with_ytdlp(video_id, preferred_lang),
        )
        _add_step(
            DEEPGRAM_ENABLED and bool(DEEPGRAM_API_KEY),
            lambda: _fetch_youtube_transcript_with_deepgram(video_id, preferred_lang),
        )
        _add_step(
            LOCAL_WHISPER_ENABLED and WhisperModel is not None,
            lambda: _fetch_youtube_transcript_with_local_whisper(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENROUTER_API_KEY),
            lambda: _fetch_youtube_transcript_with_openrouter_audio(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENAI_API_KEY),
            lambda: _fetch_youtube_transcript_with_openai(video_id, preferred_lang),
        )
    else:
        _add_step(
            YouTubeTranscriptApi is not None,
            lambda: _fetch_youtube_transcript(video_id, preferred_lang),
        )
        _add_step(
            DEEPGRAM_ENABLED and bool(DEEPGRAM_API_KEY),
            lambda: _fetch_youtube_transcript_with_deepgram(video_id, preferred_lang),
        )
        _add_step(
            yt_dlp is not None,
            lambda: _fetch_youtube_transcript_with_ytdlp(video_id, preferred_lang),
        )
        _add_step(
            LOCAL_WHISPER_ENABLED and WhisperModel is not None,
            lambda: _fetch_youtube_transcript_with_local_whisper(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENROUTER_API_KEY),
            lambda: _fetch_youtube_transcript_with_openrouter_audio(video_id, preferred_lang),
        )
        _add_step(
            bool(OPENAI_API_KEY),
            lambda: _fetch_youtube_transcript_with_openai(video_id, preferred_lang),
        )

    for step in extract_plan:
        if transcript is not None:
            break
        try:
            transcript = step()
        except Exception as exc:
            extract_errors.append(exc)

    return transcript, extract_errors


def _is_youtube_access_blocked_error(exc: Exception) -> bool:
    if not exc:
        return False
    name = exc.__class__.__name__.strip().lower()
    message = str(exc or "").strip().lower()
    haystack = f"{name} {message}"
    markers = (
        "sign in to confirm you're not a bot",
        "sign in to confirm you’re not a bot",
        "too many requests",
        "http error 429",
        "requestblocked",
        "ipblocked",
        "youtube is blocking requests from your ip",
        "use --cookies-from-browser",
        "use --cookies",
    )
    return any(marker in haystack for marker in markers)


def _build_transcript_error_response(extract_errors: list) -> tuple[dict, int]:
    names = {exc.__class__.__name__ for exc in extract_errors}
    if "VideoUnavailable" in names:
        return {"error": "Vídeo indisponível ou privado."}, 404
    if "TranscriptsDisabled" in names:
        return {
            "error": "Legendas desativadas para este vídeo. "
                     "Nem API oficial nem fallback conseguiram extrair."
        }, 404
    if "NoTranscriptFound" in names or "NoTranscriptAvailable" in names:
        return {
            "error": "Sem legendas disponíveis no idioma solicitado. "
                     "Tente mudar o idioma ou usar outro vídeo."
        }, 404
    if any(_is_youtube_access_blocked_error(exc) for exc in extract_errors):
        return {
            "error": "O YouTube bloqueou a extração automática neste ambiente "
                     "(bot check / 429 / bloqueio de IP). Isso acontece com "
                     "mais frequência em Docker e servidores. Tente rodar a "
                     "aplicação fora do container, aguardar alguns minutos, "
                     "ou configurar cookies do YouTube para o yt-dlp."
        }, 429

    for exc in extract_errors:
        if isinstance(exc, ValueError):
            return {"error": str(exc)}, 404
        if isinstance(exc, RuntimeError):
            return {"error": str(exc)}, 500

    if extract_errors:
        print("[YouTube Transcript] Falhas combinadas:", [str(e) for e in extract_errors])

    return {
        "error": "Não foi possível extrair legendas por nenhum método. "
                 "Tente outro vídeo, mude o idioma, ou habilite "
                 "DEEPGRAM_API_KEY/LOCAL_WHISPER_ENABLED/OPENAI_API_KEY para fallback de áudio."
    }, 404


def _normalize_input_transcript_segments(raw_segments) -> list[dict]:
    prepared = []
    for item in raw_segments or []:
        if not isinstance(item, dict):
            continue
        text = _clean_caption_text(str(item.get("text", "") or ""))
        if not text:
            continue

        start = _coerce_float(item.get("start"))
        if start is None:
            start = 0.0
        start = max(0.0, start)

        duration = _coerce_float(item.get("duration"))
        end = _coerce_float(item.get("end"))
        if duration is None and end is not None:
            duration = end - start
        duration = max(0.18, float(duration or 0.9))

        segment = {"text": text, "start": start, "duration": duration}
        if isinstance(item.get("words"), list):
            segment["words"] = item["words"]
        prepared.append(segment)

    segments = _normalize_transcript_segments(prepared)
    return _dedupe_overlapping_segments(segments)


FALLBACK_KEYWORD_STOPWORDS = {
    # English
    "a", "about", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "him", "his", "i", "if", "in", "into", "is", "it", "its", "just",
    "me", "my", "no", "not", "of", "on", "or", "our", "ours", "please",
    "she", "so", "that", "the", "their", "them", "there", "they", "this",
    "to", "too", "was", "we", "were", "what", "when", "where", "which", "who",
    "why", "will", "with", "would", "yeah", "yes", "you", "your", "yours",
    # Conversational fillers
    "actually", "anyway", "basically", "bye", "exactly", "first", "hello",
    "hi", "hmm", "huh", "like", "okay", "ok", "repeat", "right", "sorry",
    "step", "then", "way", "well",
    # Portuguese / Spanish / French helpers (mixed speech)
    "aliás", "alias", "assim", "com", "como", "de", "e", "em", "eu", "la",
    "mais", "mas", "nao", "não", "o", "os", "para", "por", "que", "se",
    "um", "uma", "voce", "você", "y", "el", "en", "et", "le", "les", "mais",
}


def _extract_keyword_fallback_words(text: str, limit: int) -> list[str]:
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text or "")
    if not tokens:
        return []

    counts = {}
    first_seen = {}
    first_token = {}
    for idx, token in enumerate(tokens):
        key = _analysis_word_key(token)
        if len(key) < 3:
            continue
        if key in FALLBACK_KEYWORD_STOPWORDS:
            continue
        counts[key] = counts.get(key, 0) + 1
        if key not in first_seen:
            first_seen[key] = idx
            first_token[key] = token

    if not counts:
        return []

    ranked_keys = sorted(
        counts.keys(),
        key=lambda key: (-counts[key], -len(key), first_seen[key]),
    )
    return [first_token[key] for key in ranked_keys[:max(1, int(limit or 1))]]


LOCAL_PRACTICE_SENTENCE_BANKS = {
    "en": [
        "Today I want to practice talking about {topic}.",
        "At first, the situation looked simple, but I noticed important details.",
        "I asked for feedback and tried to speak more naturally.",
        "After a few repetitions, my rhythm and confidence improved.",
        "Now I can explain this topic more clearly.",
        "My goal is to stay consistent and practice every day.",
    ],
    "pt": [
        "Hoje eu quero praticar falando sobre {topic}.",
        "No comeco, a situacao parecia simples, mas percebi detalhes importantes.",
        "Pedi feedback e tentei falar de forma mais natural.",
        "Depois de algumas repeticoes, meu ritmo e confianca melhoraram.",
        "Agora eu consigo explicar esse tema com mais clareza.",
        "Meu objetivo e manter consistencia e praticar todos os dias.",
    ],
    "es": [
        "Hoy quiero practicar hablando sobre {topic}.",
        "Al principio, la situacion parecia simple, pero note detalles importantes.",
        "Pedi comentarios y trate de hablar de forma mas natural.",
        "Despues de algunas repeticiones, mi ritmo y confianza mejoraron.",
        "Ahora puedo explicar este tema con mas claridad.",
        "Mi objetivo es mantener constancia y practicar cada dia.",
    ],
    "fr": [
        "Aujourd'hui, je veux m'entrainer a parler de {topic}.",
        "Au debut, la situation semblait simple, mais j'ai remarque des details importants.",
        "J'ai demande un retour et j'ai essaye de parler plus naturellement.",
        "Apres quelques repetitions, mon rythme et ma confiance se sont ameliores.",
        "Maintenant, je peux expliquer ce sujet plus clairement.",
        "Mon objectif est de rester regulier et de pratiquer chaque jour.",
    ],
    "de": [
        "Heute mochte ich das Sprechen uber {topic} uben.",
        "Am Anfang wirkte die Situation einfach, aber ich habe wichtige Details bemerkt.",
        "Ich habe Feedback eingeholt und naturlicher gesprochen.",
        "Nach einigen Wiederholungen haben sich Rhythmus und Sicherheit verbessert.",
        "Jetzt kann ich dieses Thema klarer erklaren.",
        "Mein Ziel ist es, konsequent zu bleiben und jeden Tag zu uben.",
    ],
    "it": [
        "Oggi voglio esercitarmi a parlare di {topic}.",
        "All'inizio la situazione sembrava semplice, ma ho notato dettagli importanti.",
        "Ho chiesto feedback e ho provato a parlare in modo piu naturale.",
        "Dopo alcune ripetizioni, ritmo e sicurezza sono migliorati.",
        "Ora riesco a spiegare questo argomento con piu chiarezza.",
        "Il mio obiettivo e mantenere costanza e praticare ogni giorno.",
    ],
}

LOCAL_DIALOGUE_BANKS = {
    "en": [
        ("Have you been practicing {topic} lately?", "Yes, a little every day."),
        ("What is the hardest part for you?", "Keeping a natural rhythm."),
        ("How do you improve your speaking?", "I repeat short phrases and record myself."),
        ("What is your next goal?", "To sound clearer and more confident."),
    ],
    "pt": [
        ("Voce tem praticado {topic} ultimamente?", "Sim, um pouco todos os dias."),
        ("Qual e a parte mais dificil para voce?", "Manter um ritmo natural."),
        ("Como voce melhora sua fala?", "Repito frases curtas e gravo minha voz."),
        ("Qual e seu proximo objetivo?", "Soar mais claro e confiante."),
    ],
    "es": [
        ("Has practicado {topic} ultimamente?", "Si, un poco cada dia."),
        ("Que parte te resulta mas dificil?", "Mantener un ritmo natural."),
        ("Como mejoras tu forma de hablar?", "Repito frases cortas y me grabo."),
        ("Cual es tu proximo objetivo?", "Sonar mas claro y con mas confianza."),
    ],
    "fr": [
        ("Tu as pratique {topic} ces derniers jours?", "Oui, un peu chaque jour."),
        ("Quelle partie est la plus difficile pour toi?", "Garder un rythme naturel."),
        ("Comment ameliores-tu ton expression orale?", "Je repete de courtes phrases et je m'enregistre."),
        ("Quel est ton prochain objectif?", "Parler plus clairement et avec confiance."),
    ],
    "de": [
        ("Hast du {topic} in letzter Zeit geubt?", "Ja, jeden Tag ein bisschen."),
        ("Was ist fur dich am schwierigsten?", "Einen naturlichen Rhythmus zu halten."),
        ("Wie verbesserst du dein Sprechen?", "Ich wiederhole kurze Satze und nehme mich auf."),
        ("Was ist dein nachstes Ziel?", "Klarer und sicherer zu klingen."),
    ],
    "it": [
        ("Hai praticato {topic} ultimamente?", "Si, un po ogni giorno."),
        ("Qual e la parte piu difficile per te?", "Mantenere un ritmo naturale."),
        ("Come migliori il tuo parlato?", "Ripeto frasi brevi e mi registro."),
        ("Qual e il tuo prossimo obiettivo?", "Parlare in modo piu chiaro e sicuro."),
    ],
}

LOCAL_CONVERSATION_REPLY_TEMPLATES = {
    "en": 'Interesting point about "{snippet}". Let us keep practicing this step by step. What would you like to add next?',
    "pt": 'Ponto interessante sobre "{snippet}". Vamos praticar isso passo a passo. O que voce gostaria de acrescentar agora?',
    "es": 'Es un punto interesante sobre "{snippet}". Vamos a practicarlo paso a paso. Que te gustaria agregar ahora?',
    "fr": 'Point interessant sur "{snippet}". Continuons a le pratiquer pas a pas. Que veux-tu ajouter maintenant?',
    "de": 'Interessanter Punkt zu "{snippet}". Lass uns das Schritt fur Schritt weiter uben. Was mochtest du jetzt erganzen?',
    "it": 'Punto interessante su "{snippet}". Continuiamo a praticarlo passo dopo passo. Cosa vuoi aggiungere adesso?',
}

LOCAL_CONVERSATION_SUGGESTIONS = {
    "en": [
        "Can you give me one concrete example?",
        "What was the most difficult part for you?",
        "How would you explain this in one short sentence?",
    ],
    "pt": [
        "Pode me dar um exemplo concreto?",
        "Qual foi a parte mais dificil para voce?",
        "Como voce explicaria isso em uma frase curta?",
    ],
    "es": [
        "Puedes darme un ejemplo concreto?",
        "Cual fue la parte mas dificil para ti?",
        "Como explicarias esto en una frase corta?",
    ],
    "fr": [
        "Peux-tu me donner un exemple concret?",
        "Quelle a ete la partie la plus difficile pour toi?",
        "Comment expliquerais-tu cela en une phrase courte?",
    ],
    "de": [
        "Kannst du mir ein konkretes Beispiel geben?",
        "Was war fur dich der schwierigste Teil?",
        "Wie wurdest du das in einem kurzen Satz erklaren?",
    ],
    "it": [
        "Puoi farmi un esempio concreto?",
        "Qual e stata la parte piu difficile per te?",
        "Come lo spiegheresti in una frase breve?",
    ],
}


def _build_local_practice_payload(topic: str,
                                  target_lang: str,
                                  text_length: str,
                                  text_type: str,
                                  focus: str) -> dict:
    normalized_lang = _normalize_study_target_lang(target_lang, default="en")
    rules = PRACTICE_LENGTH_RULES.get(text_length) or PRACTICE_LENGTH_RULES["medium"]
    sentence_count = max(1, int(rules.get("max") or 6))
    safe_topic = _clean_caption_text(topic or "")[:90] or "everyday situations"

    if text_type in {"dialogue", "interview", "casual_chat"}:
        pairs = LOCAL_DIALOGUE_BANKS.get(normalized_lang) or LOCAL_DIALOGUE_BANKS["en"]
        lines = []
        idx = 0
        while len(lines) < sentence_count:
            question, answer = pairs[idx % len(pairs)]
            lines.append(f"A: {question.format(topic=safe_topic)}")
            if len(lines) >= sentence_count:
                break
            lines.append(f"B: {answer}")
            idx += 1
        text = "\n".join(lines[:sentence_count]).strip()
    else:
        bank = LOCAL_PRACTICE_SENTENCE_BANKS.get(normalized_lang) or LOCAL_PRACTICE_SENTENCE_BANKS["en"]
        parts = []
        idx = 0
        while len(parts) < sentence_count:
            template = bank[idx % len(bank)]
            parts.append(template.format(topic=safe_topic))
            idx += 1
        text = " ".join(parts).strip()

    title_prefix = {
        "en": "Practice",
        "pt": "Pratica",
        "es": "Practica",
        "fr": "Pratique",
        "de": "Ubung",
        "it": "Pratica",
    }.get(normalized_lang, "Practice")
    title = f"{title_prefix}: {safe_topic}"

    focus_points = []
    requested_focus = _clean_caption_text(focus or "")
    if requested_focus and requested_focus.casefold() not in {"general fluency", "fluencia geral"}:
        focus_points.append(f"Foco solicitado: {requested_focus}.")
    focus_points.extend([
        "Repita em voz alta 3 vezes, mantendo ritmo estavel.",
        "Conecte as palavras sem pausas longas entre elas.",
        "Grave sua voz e compare com o audio-modelo.",
    ])
    focus_points = focus_points[:4]

    keywords = _extract_keyword_fallback_words(text, limit=5)
    vocabulary_preview = [
        {"word": word, "meaning": "Termo relevante ao tema em contexto."}
        for word in keywords
    ]

    return {
        "title": title,
        "text": _enforce_practice_text_length(text, text_length),
        "focus_points": focus_points,
        "vocabulary_preview": vocabulary_preview,
    }


def _build_local_conversation_reply(user_text: str, lang: str, history: list[dict]) -> str:
    normalized_lang = _normalize_lang(lang, default="en")
    snippet = _clean_caption_text(user_text or "").replace('"', "'").strip()
    if len(snippet) > 72:
        snippet = snippet[:72].rstrip() + "..."
    if not snippet:
        snippet = {
            "pt": "isso",
            "en": "that",
            "es": "eso",
            "fr": "ca",
            "de": "das",
            "it": "questo",
        }.get(normalized_lang, "that")

    template = LOCAL_CONVERSATION_REPLY_TEMPLATES.get(normalized_lang)
    if not template:
        template = LOCAL_CONVERSATION_REPLY_TEMPLATES["en"]

    reply = template.format(snippet=snippet)
    if history and len(history) % 2 == 0:
        follow_ups = {
            "pt": "Voce pode me contar um exemplo rapido?",
            "en": "Can you share one quick example?",
            "es": "Puedes compartir un ejemplo rapido?",
            "fr": "Tu peux donner un exemple rapide?",
            "de": "Kannst du ein kurzes Beispiel geben?",
            "it": "Puoi condividere un esempio rapido?",
        }
        reply = f"{reply} {follow_ups.get(normalized_lang, follow_ups['en'])}"
    return reply


def _local_conversation_suggestions(lang: str) -> list[str]:
    normalized_lang = _normalize_lang(lang, default="en")
    suggestions = LOCAL_CONVERSATION_SUGGESTIONS.get(normalized_lang)
    if suggestions:
        return suggestions[:3]
    return LOCAL_CONVERSATION_SUGGESTIONS["en"][:3]


def _normalize_conversation_suggestions(raw_items, limit: int = 3) -> list[str]:
    try:
        max_items = max(1, min(6, int(limit or 1)))
    except (TypeError, ValueError):
        max_items = 3

    values = raw_items
    if isinstance(values, dict):
        values = (
            values.get("next_reply_suggestions")
            or values.get("suggestions")
            or values.get("responses")
            or values.get("items")
            or values.get("options")
            or []
        )
    if isinstance(values, str):
        values = [
            part.strip(" -•\t")
            for part in re.split(r"[\n;]+", values)
            if part and part.strip()
        ]
    if not isinstance(values, list):
        return []

    normalized = []
    seen = set()
    for item in values:
        if isinstance(item, dict):
            text = _clean_caption_text(
                item.get("text")
                or item.get("phrase")
                or item.get("suggestion")
                or ""
            )
        else:
            text = _clean_caption_text(item)
        if not text:
            continue
        text = re.sub(r"^[\-\d\)\.\s]+", "", text).strip()
        key = text.casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(text)
        if len(normalized) >= max_items:
            break
    return normalized


def _conversation_generate_reply_suggestions(history: list[dict],
                                             lang: str,
                                             *,
                                             latest_ai_text: str = "",
                                             limit: int = 3,
                                             force_local: bool = False) -> list[str]:
    try:
        max_items = max(1, min(6, int(limit or 1)))
    except (TypeError, ValueError):
        max_items = 3

    fallback = _local_conversation_suggestions(lang)[:max_items]
    if force_local or not has_text_ai_provider():
        return fallback

    normalized_lang = _normalize_lang(lang, default="en")
    recent = history[-8:] if isinstance(history, list) and len(history) > 8 else (history or [])
    context_lines = []
    for msg in recent:
        if not isinstance(msg, dict):
            continue
        role = _normalize_conversation_role(msg.get("role"))
        text = _clean_caption_text(
            msg.get("content")
            or msg.get("original")
            or msg.get("text")
            or ""
        )
        if not text:
            continue
        speaker = "Alex" if role == "ai" else "Student"
        context_lines.append(f"{speaker}: {text}")

    latest_ai_clean = _clean_caption_text(latest_ai_text or "")
    if latest_ai_clean:
        latest_line = f"Alex: {latest_ai_clean}"
        if not context_lines or context_lines[-1].casefold() != latest_line.casefold():
            context_lines.append(latest_line)

    if not context_lines:
        return fallback

    lang_label = PRACTICE_LANG_LABELS.get(normalized_lang, normalized_lang.upper())
    suggest_system = (
        f"You are a language coach helping a Brazilian student practice {lang_label}."
    )
    suggest_prompt = (
        f"Conversation so far (in {lang_label}):\n"
        + "\n".join(context_lines)
        + "\n\n"
        + f"Generate exactly {max_items} short, natural phrases the student could say next in {lang_label}. "
        + "Each phrase must:\n"
        + "- be 5-12 words\n"
        + "- sound natural for spoken conversation\n"
        + "- vary direction (continue, ask, slightly shift topic)\n"
        + "Return ONLY a JSON array of strings. No markdown."
    )
    try:
        raw_suggestions, _ = chat_with_fallback(
            suggest_system,
            suggest_prompt,
            max_tokens=180,
            temperature=0.75,
        )
    except Exception:
        return fallback

    parsed = _extract_json_payload_from_text(raw_suggestions or "")
    candidate = parsed if parsed is not None else raw_suggestions
    if isinstance(candidate, dict) and "segments" in candidate:
        candidate = candidate["segments"]
    suggestions = _normalize_conversation_suggestions(candidate, limit=max_items)
    return suggestions or fallback


def _normalize_study_compare_text(text: str) -> str:
    raw = _clean_caption_text(text or "")
    if not raw:
        return ""
    folded = raw.casefold()
    folded = re.sub(r"[^\wÀ-ÖØ-öø-ÿ]+", "", folded, flags=re.UNICODE)
    return folded


def _study_texts_too_similar(left: str, right: str) -> bool:
    left_norm = _normalize_study_compare_text(left)
    right_norm = _normalize_study_compare_text(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    ratio = difflib.SequenceMatcher(a=left_norm, b=right_norm).ratio()
    return ratio >= 0.9


def _sanitize_study_pronunciation(pronunciation: str,
                                  translation: str,
                                  phrase_text: str,
                                  source_lang: str,
                                  target_lang: str) -> str:
    pron = _clean_caption_text(pronunciation or "")
    translated = _clean_caption_text(translation or "")
    source_text = _clean_caption_text(phrase_text or "")
    src_base = str(source_lang or "").split("-")[0].lower()
    tgt_base = str(target_lang or "").split("-")[0].lower()

    if not pron:
        return source_text or translated

    # Se a pronúncia veio igual (ou quase igual) à tradução em idioma diferente,
    # preferimos o texto original para evitar duplicar o conteúdo.
    if src_base and tgt_base and src_base != tgt_base:
        if _study_texts_too_similar(pron, translated):
            return source_text or pron

    return pron


def _backfill_study_translation_pronunciation(phrases: list[dict],
                                              source_lang: str,
                                              target_lang: str) -> dict[int, dict]:
    """Preenche tradução/pronúncia faltantes em lote com uma chamada curta de IA."""
    if not phrases:
        return {}

    payload = [
        {
            "phrase_index": _coerce_int(item.get("phrase_index"), default=-1, min_value=-1, max_value=9999),
            "text": _clean_caption_text(item.get("text", "")),
        }
        for item in phrases
    ]
    payload = [item for item in payload if item["phrase_index"] >= 0 and item["text"]]
    if not payload:
        return {}

    system_prompt = f"""Você é um professor de idiomas.
Idioma original: {source_lang or "en"}.
Idioma da tradução: {target_lang}.

Retorne APENAS JSON válido:
{{
  "phrases": [
    {{
      "phrase_index": 0,
      "translation": "tradução natural e curta",
      "pronunciation": "pronúncia simplificada para brasileiro (PT-BR)"
    }}
  ]
}}

Regras:
- Preencha TODOS os itens recebidos.
- Nunca deixe translation ou pronunciation vazios.
- Não invente conteúdo fora da frase."""

    user_message = (
        "Complete tradução e pronúncia para os itens abaixo:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    result, _provider = chat_with_fallback(
        system_prompt,
        user_message,
        max_tokens=2200,
        temperature=0.0,
    )
    if not result:
        return {}

    parsed = _extract_json_payload_from_text(result) or {}
    if isinstance(parsed, list):
        raw_items = parsed
    else:
        raw_items = (
            parsed.get("phrases")
            or parsed.get("items")
            or parsed.get("segments")
            or []
        )
    if not isinstance(raw_items, list):
        return {}

    allowed = {item["phrase_index"] for item in payload}
    filled = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        idx = _coerce_int(item.get("phrase_index"), default=-1, min_value=-1, max_value=9999)
        if idx not in allowed:
            continue
        translation = _clean_caption_text(
            item.get("translation")
            or item.get("meaning")
            or ""
        )
        pronunciation = _clean_caption_text(
            item.get("pronunciation")
            or item.get("phonetic")
            or ""
        )
        if translation or pronunciation:
            filled[idx] = {
                "translation": translation,
                "pronunciation": pronunciation,
            }
    return filled


def _build_youtube_transcript_study(segments: list[dict],
                                    source_lang: str,
                                    target_lang: str = "pt",
                                    max_segments: int = MAX_STUDY_SEGMENTS,
                                    max_words_per_phrase: int = MAX_STUDY_WORDS) -> dict:
    if not segments:
        raise ValueError("Transcrição vazia para estudo.")

    selected = []
    for idx, seg in enumerate(segments):
        text = _clean_caption_text(seg.get("text", ""))
        if not text:
            continue
        start = round(float(seg.get("start", 0.0) or 0.0), 3)
        end = round(float(seg.get("end", start + float(seg.get("duration", 0.9) or 0.9))), 3)
        selected.append({
            "phrase_index": idx,
            "text": text,
            "start": start,
            "end": max(start + 0.18, end),
        })
        if len(selected) >= max_segments:
            break

    if not selected:
        raise ValueError("Nenhuma frase válida para estudo.")

    system_prompt = f"""Você é um professor de idiomas focado em shadowing.
Idioma da transcrição: {source_lang or "en"}.
Idioma de saída (tradução): {target_lang}.

Retorne APENAS JSON válido (sem markdown/código):
{{
  "lesson_intro": "explicação curta estilo professor sobre como estudar este trecho",
  "phrases": [
    {{
      "phrase_index": 0,
      "translation": "tradução natural da frase",
      "pronunciation": "pronúncia simplificada para brasileiro (PT-BR)",
      "teacher_explanation": "explicação didática curta, falando diretamente com o aluno",
      "notes": "dica curta de pronúncia/entonação",
      "words": [
        {{
          "word": "palavra original",
          "meaning": "significado contextual em {target_lang}",
          "translation": "tradução curta",
          "pronunciation": "pronúncia simplificada para brasileiro"
        }}
      ]
    }}
  ]
}}

Regras:
- Inclua no máximo {max_words_per_phrase} palavras por frase.
- Não invente termos fora da frase.
- Use linguagem curta e objetiva.
- Escreva em tom de professor acolhedor e claro.
- Em cada "teacher_explanation", explique como praticar a frase (ritmo, entonacao ou ligacao de sons)."""

    user_msg = (
        f"Analise estas frases por índice e devolva o JSON no formato pedido.\n"
        f"Frases:\n{json.dumps(selected, ensure_ascii=False)}"
    )
    can_use_ai = has_text_ai_provider()
    provider = "fallback"
    parsed = {}
    raw_items = []
    warning = ""
    if can_use_ai:
        result, provider_name = chat_with_cloud_fallback(
            system_prompt,
            user_msg,
            max_tokens=3200,
            temperature=0.2,
        )
        if not result:
            # Último recurso local: Ollama (somente após cloud falhar).
            result = ollama_chat(
                system_prompt,
                user_msg,
                model="",
                max_tokens=3200,
                temperature=0.2,
            )
            if result:
                provider_name = "ollama"
        if provider_name:
            provider = provider_name
        if result:
            extracted = _extract_json_payload_from_text(result) or {}
            if isinstance(extracted, list):
                raw_items = extracted
            elif isinstance(extracted, dict):
                parsed = extracted
                raw_items = (
                    extracted.get("phrases")
                    or extracted.get("items")
                    or extracted.get("segments")
                    or []
                )
                if not isinstance(raw_items, list):
                    raw_items = []
            if not raw_items:
                warning = (
                    "Resposta da IA em formato inesperado. "
                    "Aplicado fallback local para completar o estudo."
                )
        else:
            warning = (
                "DeepSeek/OpenRouter/OpenAI/Ollama indisponível no momento. "
                "Aplicado fallback local para gerar o estudo."
            )
    else:
        warning = (
            "Nenhum provedor de IA textual disponível. "
            "Aplicado fallback local para gerar o estudo."
        )

    lesson_intro = _clean_caption_text(
        parsed.get("lesson_intro")
        or parsed.get("intro")
        or parsed.get("teacher_intro")
        or ""
    )

    allowed_indexes = {item["phrase_index"] for item in selected}
    study_by_idx = {}

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        idx = _coerce_int(item.get("phrase_index"), default=-1, min_value=-1, max_value=9999)
        if idx not in allowed_indexes:
            continue

        words = []
        seen_words = set()
        for raw_word in item.get("words") or []:
            if not isinstance(raw_word, dict):
                continue
            word = _clean_caption_text(raw_word.get("word") or raw_word.get("term") or "")
            if not word:
                continue
            key = word.casefold()
            if key in seen_words:
                continue
            seen_words.add(key)
            words.append({
                "word": word,
                "meaning": _clean_caption_text(
                    raw_word.get("meaning") or raw_word.get("definition") or ""
                ),
                "translation": _clean_caption_text(raw_word.get("translation") or ""),
                "pronunciation": _clean_caption_text(
                    raw_word.get("pronunciation") or raw_word.get("phonetic") or ""
                ),
            })
            if len(words) >= max_words_per_phrase:
                break

        study_by_idx[idx] = {
            "translation": _clean_caption_text(item.get("translation") or ""),
            "pronunciation": _clean_caption_text(
                item.get("pronunciation") or item.get("phonetic") or ""
            ),
            "teacher_explanation": _clean_caption_text(
                item.get("teacher_explanation")
                or item.get("explanation")
                or item.get("coach_note")
                or ""
            ),
            "notes": _clean_caption_text(item.get("notes") or item.get("tip") or ""),
            "words": words,
        }

    missing_translation_or_pron = []
    for phrase in selected:
        idx = phrase["phrase_index"]
        ai = study_by_idx.get(idx, {})
        if not ai.get("translation") or not ai.get("pronunciation"):
            missing_translation_or_pron.append({
                "phrase_index": idx,
                "text": phrase["text"],
            })

    if missing_translation_or_pron and can_use_ai:
        backfilled = _backfill_study_translation_pronunciation(
            missing_translation_or_pron,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        for item in missing_translation_or_pron:
            idx = item["phrase_index"]
            current = study_by_idx.setdefault(idx, {
                "translation": "",
                "pronunciation": "",
                "teacher_explanation": "",
                "notes": "",
                "words": [],
            })
            extra = backfilled.get(idx, {})
            if not current.get("translation"):
                current["translation"] = _clean_caption_text(extra.get("translation") or "")
            if not current.get("pronunciation"):
                current["pronunciation"] = _clean_caption_text(extra.get("pronunciation") or "")

    phrases = []
    for phrase in selected:
        ai = study_by_idx.get(phrase["phrase_index"], {})
        words = ai.get("words") or []
        if not words:
            fallback_words = _extract_keyword_fallback_words(
                phrase["text"],
                limit=max(2, min(max_words_per_phrase, 4)),
            )
            words = [
                {
                    "word": token,
                    "meaning": "",
                    "translation": "",
                    "pronunciation": "",
                }
                for token in fallback_words
            ]
        normalized_words = []
        for word_item in words:
            if not isinstance(word_item, dict):
                continue
            word_text = _clean_caption_text(word_item.get("word") or "")
            if not word_text:
                continue
            word_translation = _clean_caption_text(
                word_item.get("translation")
                or word_item.get("meaning")
                or ""
            )
            word_pron = _sanitize_study_pronunciation(
                word_item.get("pronunciation") or "",
                word_translation,
                word_text,
                source_lang=source_lang,
                target_lang=target_lang,
            )
            normalized_words.append({
                "word": word_text,
                "meaning": _clean_caption_text(word_item.get("meaning") or ""),
                "translation": _clean_caption_text(word_item.get("translation") or ""),
                "pronunciation": word_pron,
            })
        words = normalized_words

        teacher_explanation = ai.get("teacher_explanation", "")
        if not teacher_explanation:
            translation_hint = ai.get("translation", "")
            if translation_hint:
                teacher_explanation = (
                    f'Professor explica: esta frase significa "{translation_hint}". '
                    "Repita em voz alta com ritmo natural e conecte os sons entre as palavras."
                )
            else:
                teacher_explanation = (
                    "Professor explica: entenda a ideia geral e repita a frase 3 vezes, "
                    "mantendo ritmo natural e entonacao clara."
                )

        translation = _clean_caption_text(ai.get("translation", ""))
        pronunciation = _sanitize_study_pronunciation(
            ai.get("pronunciation", ""),
            translation,
            phrase["text"],
            source_lang=source_lang,
            target_lang=target_lang,
        )

        if not translation:
            src_base = str(source_lang or "").split("-")[0].lower()
            tgt_base = str(target_lang or "").split("-")[0].lower()
            translation = phrase["text"] if src_base and src_base == tgt_base else "Tradução indisponível."
        if not pronunciation:
            pronunciation = phrase["text"]

        phrases.append({
            "phrase_index": phrase["phrase_index"],
            "start": phrase["start"],
            "end": phrase["end"],
            "text": phrase["text"],
            "translation": translation,
            "pronunciation": pronunciation,
            "teacher_explanation": teacher_explanation,
            "notes": ai.get("notes", ""),
            "words": words,
        })

    if not lesson_intro:
        lesson_intro = (
            "Professor explica: leia cada frase em voz alta, repita com ritmo natural, "
            "e use as palavras destacadas para ampliar vocabulário em contexto."
        )

    return {
        "lesson_intro": lesson_intro,
        "phrases": phrases,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "segments_analyzed": len(selected),
        "ai_provider": provider or "fallback",
        "warning": warning,
    }


@app.errorhandler(BadRequest)
def handle_bad_request(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": exc.description or "Requisição inválida."}), 400
    return exc


@app.errorhandler(404)
def handle_not_found(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Rota não encontrada."}), 404
    return exc


@app.errorhandler(405)
def handle_method_not_allowed(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Método não permitido para esta rota."}), 405
    return exc


@app.errorhandler(413)
def handle_payload_too_large(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Payload muito grande para processamento."}), 413
    return exc


@app.errorhandler(500)
def handle_internal_server_error(exc):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Erro interno no servidor."}), 500
    return exc


# ──────────────────────────────────────────────────────────────
# Rotas — Páginas
# ──────────────────────────────────────────────────────────────
@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/")
def index():
    return render_template("index.html")


# ──────────────────────────────────────────────────────────────
# API — Vozes LMNT
# ──────────────────────────────────────────────────────────────
@app.route("/api/voices", methods=["GET"])
def get_voices():
    voices = lmnt_list_voices()
    return jsonify({
        "voices": voices,
        "has_lmnt": bool(LMNT_API_KEY),
        "has_piper": piper_available(),
        "piper_langs": piper_supported_languages(),
        "piper_models": piper_local_models(),
        "piper_profiles": [
            {"id": key, "label": value}
            for key, value in PIPER_PROFILE_LABELS.items()
        ],
        "piper_lexicon_path": str(PIPER_LEXICON_PATH),
        "piper_voice_overrides_path": str(PIPER_VOICE_OVERRIDES_PATH),
    })


# ──────────────────────────────────────────────────────────────
# API — Gerar sessão completa
# ──────────────────────────────────────────────────────────────
@app.route("/api/generate", methods=["POST"])
def generate_session():
    data = _require_json_object()
    text = _normalize_text_field(data.get("text"), "Texto")
    detected_lang = _detect_language(text)
    lang = _normalize_lang(data.get("lang"), default=detected_lang)
    piper_options = _build_piper_request_options(
        data,
        default_context_hint="shadowing_practice_session",
        default_profile="story",
    )
    learner = _build_learner_context(data, default_lang=lang)
    voice = _normalize_text_field(
        data.get("voice", "leah"),
        "Voz",
        required=False,
        max_chars=48,
    ) or "leah"
    requested_tts_engine = _normalize_tts_engine(
        data.get("tts_engine"),
        use_lmnt=data.get("use_lmnt"),
        default="local",
    )

    # 1) Gerar áudio
    audio_id = str(uuid.uuid4())[:8]
    audio_filename = ""
    audio_path = None
    tts_engine = ""
    word_durations = None
    piper_meta = None

    audio_bytes = None
    if requested_tts_engine == "lmnt":
        if LMNT_API_KEY:
            audio_bytes, word_durations = lmnt_synthesize_with_durations(
                text, voice=voice, lang=lang
            )
        if not audio_bytes:
            audio_bytes = deepgram_synthesize(text, lang=lang)
            if audio_bytes:
                tts_engine = "deepgram"
    elif requested_tts_engine == "deepgram":
        audio_bytes = deepgram_synthesize(text, lang=lang)
        if not audio_bytes and LMNT_API_KEY:
            audio_bytes, word_durations = lmnt_synthesize_with_durations(
                text, voice=voice, lang=lang
            )
            if audio_bytes:
                tts_engine = "lmnt"
    else:
        # local/piper only
        audio_bytes = None

    if audio_bytes:
        audio_filename = f"shadow_{audio_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        audio_path.write_bytes(audio_bytes)
        if not tts_engine:
            tts_engine = requested_tts_engine if requested_tts_engine in {"lmnt", "deepgram"} else "lmnt"
    else:
        piper_filename = f"shadow_{audio_id}.wav"
        piper_path = AUDIO_DIR / piper_filename
        piper_result = piper_synthesize_to_file(
            text,
            piper_path,
            lang=lang,
            request_options=piper_options,
        )
        if piper_result.get("ok"):
            audio_filename = piper_filename
            audio_path = piper_path
            tts_engine = "piper"
            piper_meta = _public_piper_meta(piper_result)

    if not audio_path:
        model_path, _ = _piper_model_and_config_for_lang(lang)
        model_name = model_path.name if model_path else "nenhum modelo Piper configurado"
        return jsonify({
            "error": (
                "Não foi possível gerar áudio. "
                "Ative LMNT/Deepgram ou configure Piper local "
                f"para o idioma '{lang}' ({model_name})."
            )
        }), 500

    # 2) Buscar vídeos virais
    search_query = _clean_text_for_search(text)
    search_query += " English speaking viral" if lang == "en" else " viral"

    videos, video_source, video_search_error = _search_youtube_videos(
        search_query,
        lang=lang,
        max_results=6,
        allow_generic_fallback=True,
    )
    video_warning = ""
    if not videos:
        video_warning = (
            "YouTube indisponível no momento. Tente novamente ou use a busca manual."
        )
        print(f"[YouTube] Busca sem resultados: {video_search_error}")

    # 3) Dividir texto em frases
    sentences = re.split(r'(?<=[.!?。！？])\s+|\n+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    response = {
        "audio_url": url_for("static", filename=f"audio/{audio_filename}"),
        "text": text,
        "sentences": sentences,
        "language": lang,
        "voice": voice,
        "tts_engine": tts_engine,
        "videos": videos,
        "video_source": video_source,
        "video_warning": video_warning,
        "session_id": audio_id,
        "durations": word_durations,
    }
    if piper_meta:
        response["piper_meta"] = piper_meta
    _ADAPTIVE_STORE.record_event(
        learner=learner,
        event_type="practice_session_generated",
        skill_area="shadowing",
        duration_sec=0,
        content_ref=tts_engine,
        content_text=text,
        payload={
            "sentence_count": len(sentences),
            "tts_engine": tts_engine,
            "voice": voice,
        },
    )
    return jsonify(response)

    # Note: session history is saved client-side via /api/history


# ──────────────────────────────────────────────────────────────
# API — TTS frase individual
# ──────────────────────────────────────────────────────────────
@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    data = _require_json_object()
    text = _normalize_text_field(data.get("text"), "Texto")
    lang = _normalize_lang(data.get("lang"), default="en")
    piper_options = _build_piper_request_options(
        data,
        default_context_hint="study_phrase",
        default_profile="lesson",
    )
    voice = _normalize_text_field(
        data.get("voice", "leah"),
        "Voz",
        required=False,
        max_chars=48,
    ) or "leah"
    requested_tts_engine = _normalize_tts_engine(
        data.get("tts_engine"),
        use_lmnt=data.get("use_lmnt"),
        default="local",
    )

    audio_id = str(uuid.uuid4())[:8]
    audio_filename = ""
    audio_path = None
    tts_engine = ""
    piper_meta = None

    audio_bytes = None
    if requested_tts_engine == "lmnt":
        if LMNT_API_KEY:
            audio_bytes = lmnt_synthesize(text, voice=voice, lang=lang)
        if not audio_bytes:
            audio_bytes = deepgram_synthesize(text, lang=lang)
            if audio_bytes:
                tts_engine = "deepgram"
    elif requested_tts_engine == "deepgram":
        audio_bytes = deepgram_synthesize(text, lang=lang)
        if not audio_bytes and LMNT_API_KEY:
            audio_bytes = lmnt_synthesize(text, voice=voice, lang=lang)
            if audio_bytes:
                tts_engine = "lmnt"
    else:
        # local/piper only
        audio_bytes = None

    if audio_bytes:
        audio_filename = f"phrase_{audio_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        audio_path.write_bytes(audio_bytes)
        if not tts_engine:
            tts_engine = requested_tts_engine if requested_tts_engine in {"lmnt", "deepgram"} else "lmnt"
    else:
        piper_filename = f"phrase_{audio_id}.wav"
        piper_path = AUDIO_DIR / piper_filename
        piper_result = piper_synthesize_to_file(
            text,
            piper_path,
            lang=lang,
            request_options=piper_options,
        )
        if piper_result.get("ok"):
            audio_filename = piper_filename
            audio_path = piper_path
            tts_engine = "piper"
            piper_meta = _public_piper_meta(piper_result)

    if not audio_path:
        model_path, _ = _piper_model_and_config_for_lang(lang)
        model_name = model_path.name if model_path else "nenhum modelo Piper configurado"
        return jsonify({
            "error": (
                "Não foi possível gerar áudio. "
                "Ative LMNT/Deepgram ou configure Piper local "
                f"para o idioma '{lang}' ({model_name})."
            )
        }), 500

    response = {
        "audio_url": url_for("static", filename=f"audio/{audio_filename}"),
        "tts_engine": tts_engine,
    }
    if piper_meta:
        response["piper_meta"] = piper_meta
    return jsonify(response)


# ──────────────────────────────────────────────────────────────
# API — Análise inteligente (DeepSeek/OpenRouter/OpenAI/Ollama)
# ──────────────────────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze_text():
    data = _require_json_object()
    text = _normalize_text_field(data.get("text"), "Texto")
    lang = _normalize_lang(data.get("lang"), default="en")
    learner = _build_learner_context(data, default_lang=lang)
    lang_label = PRACTICE_LANG_LABELS.get(lang, lang.upper())

    if not has_text_ai_provider():
        fallback_analysis = _normalize_ai_analysis({}, text, lang)
        _ADAPTIVE_STORE.record_practice_analysis(
            learner,
            text=text,
            analysis=fallback_analysis,
        )
        return jsonify({
            "analysis": fallback_analysis,
            "provider": "fallback_local",
            "warning": "IA textual indisponivel. Analise basica local ativada.",
        })

    system_prompt = f"""Você é um coach especialista em shadowing e fluência.
O aluno é brasileiro estudando principalmente inglês.
Idioma do texto recebido: {lang_label} ({lang}).

Regras de qualidade obrigatórias:
- Use APENAS palavras e frases que realmente existem no texto enviado.
- Não invente termos, exemplos ou frases fora do texto.
- Em "key_vocabulary.example", escreva exemplo no MESMO idioma do texto.
- Em "phonetic", nunca use placeholder como "IPA".
- Se o idioma for inglês (en), trate explicitamente como aula de inglês.

Analise o texto e retorne APENAS um JSON válido (sem markdown, sem code fences):
{{
  "difficulty_level": "beginner|intermediate|advanced",
  "difficulty_score": 1-5,
  "pronunciation_tips": [
    {{"word": "palavra", "phonetic": "IPA ou simplificação", "tip": "dica em português"}}
  ],
  "linking_sounds": [
    {{"phrase": "trecho do texto", "how": "pronúncia conectada", "tip": "explicação"}}
  ],
  "key_vocabulary": [
    {{"word": "word", "meaning": "significado em PT", "example": "frase no idioma do texto"}}
  ],
  "intonation_notes": "observações sobre entonação e ritmo",
  "shadowing_focus": ["3-5 pontos para focar nesta sessão"],
  "common_mistakes_br": ["erros comuns de brasileiros com este texto"]
}}

Se não souber um campo, seja conservador e não invente."""

    user_msg = (
        f"Idioma (code): {lang}\n"
        "Objetivo do aluno: melhorar compreensão, pronúncia, ritmo e entonação.\n\n"
        f"Texto:\n{text}"
    )
    result, provider = chat_with_fallback(
        system_prompt,
        user_msg,
        max_tokens=2200,
        temperature=0.15,
    )

    if not result:
        fallback_analysis = _normalize_ai_analysis({}, text, lang)
        _ADAPTIVE_STORE.record_practice_analysis(
            learner,
            text=text,
            analysis=fallback_analysis,
        )
        return jsonify({
            "analysis": fallback_analysis,
            "provider": "fallback_local",
            "warning": "Falha temporaria da IA textual. Analise basica local ativada.",
        })

    parsed = _extract_json_payload_from_text(result) or {}
    analysis = _normalize_ai_analysis(parsed, text, lang)
    _ADAPTIVE_STORE.record_practice_analysis(
        learner,
        text=text,
        analysis=analysis,
    )

    return jsonify({"analysis": analysis, "provider": provider or "unknown"})


# ──────────────────────────────────────────────────────────────
# API — Gerar prática com IA
# ──────────────────────────────────────────────────────────────
@app.route("/api/generate-practice", methods=["POST"])
def generate_practice():
    data = _require_json_object()
    topic = _normalize_text_field(
        data.get("topic", "everyday conversation"),
        "Tema",
        required=False,
        max_chars=MAX_TOPIC_CHARS,
    ) or "everyday conversation"
    level = _normalize_text_field(
        data.get("level", "intermediate"),
        "Nível",
        required=False,
        max_chars=40,
    ) or "intermediate"
    focus = _normalize_text_field(
        data.get("focus", "general fluency"),
        "Foco",
        required=False,
        max_chars=MAX_FOCUS_CHARS,
    ) or "general fluency"
    target_lang = _normalize_practice_lang(data.get("target_lang"), default="en")
    learner = _build_learner_context(data, default_lang=target_lang)
    target_lang_label = PRACTICE_LANG_LABELS.get(target_lang, target_lang.upper())
    text_length = _normalize_practice_length(data.get("text_length"), default="medium")
    length_rule = PRACTICE_LENGTH_RULES[text_length]
    text_type = _normalize_practice_type(data.get("text_type"), default="dialogue")
    text_type_label = PRACTICE_TYPE_LABELS[text_type]
    fallback_practice = _build_local_practice_payload(
        topic=topic,
        target_lang=target_lang,
        text_length=text_length,
        text_type=text_type,
        focus=focus,
    )

    if not has_text_ai_provider():
        _ADAPTIVE_STORE.record_practice_generation(
            learner,
            topic=topic,
            text_type=text_type,
            text_length=text_length,
            focus=focus,
            generated_text=fallback_practice.get("text", ""),
        )
        return jsonify({
            "practice": fallback_practice,
            "provider": "fallback_local",
            "target_lang": target_lang,
            "text_length": text_length,
            "text_type": text_type,
            "warning": "IA textual indisponivel. Texto local basico gerado.",
        })

    system_prompt = f"""Você gera material para prática de shadowing.
O aluno é brasileiro. Nível: {level}. Idioma alvo: {target_lang_label} ({target_lang}).
Tipo de texto: {text_type_label}. Tamanho: {length_rule["label"]} ({length_rule["sentences"]}).

Retorne APENAS um JSON válido (sem markdown, sem code fences):
{{
  "title": "título curto do exercício",
  "text": "texto no idioma alvo com o tamanho solicitado",
  "focus_points": ["pontos de atenção para o shadowing (em português)"],
  "vocabulary_preview": [
    {{"word": "palavra no idioma alvo", "meaning": "significado em PT"}}
  ]
}}

Regras obrigatórias:
- O campo "text" deve estar EXCLUSIVAMENTE no idioma alvo ({target_lang_label}).
- Não misture com português, a menos que o idioma alvo seja português.
- O texto deve seguir o tipo solicitado: {text_type_label}.
- O texto deve seguir o tamanho solicitado: {length_rule["sentences"]}.
- O texto deve soar natural, como um falante nativo diria.
- "focus_points" e "meaning" devem ficar em português do Brasil."""

    user_msg = (
        f"Tema: {topic}\n"
        f"Foco: {focus}\n"
        f"Idioma alvo (code): {target_lang}\n"
        f"Tamanho (code): {text_length}\n"
        f"Tipo (code): {text_type}"
    )
    result, provider = chat_with_fallback(system_prompt, user_msg)

    if not result:
        _ADAPTIVE_STORE.record_practice_generation(
            learner,
            topic=topic,
            text_type=text_type,
            text_length=text_length,
            focus=focus,
            generated_text=fallback_practice.get("text", ""),
        )
        return jsonify({
            "practice": fallback_practice,
            "provider": "fallback_local",
            "target_lang": target_lang,
            "text_length": text_length,
            "text_type": text_type,
            "warning": "Falha temporaria da IA textual. Texto local basico gerado.",
        })

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
        practice = json.loads(cleaned)
    except json.JSONDecodeError:
        practice = {"text": result}

    if not isinstance(practice, dict):
        practice = {}
    practice.setdefault("title", fallback_practice.get("title"))

    original_text = str(practice.get("text", "") or "")
    if original_text.strip():
        practice["text"] = _enforce_practice_text_length(original_text, text_length)
    else:
        practice["text"] = fallback_practice["text"]

    focus_points = practice.get("focus_points")
    if not isinstance(focus_points, list) or not focus_points:
        practice["focus_points"] = fallback_practice.get("focus_points", [])

    vocabulary_preview = practice.get("vocabulary_preview")
    if not isinstance(vocabulary_preview, list) or not vocabulary_preview:
        practice["vocabulary_preview"] = fallback_practice.get("vocabulary_preview", [])

    _ADAPTIVE_STORE.record_practice_generation(
        learner,
        topic=topic,
        text_type=text_type,
        text_length=text_length,
        focus=focus,
        generated_text=practice.get("text", ""),
    )

    return jsonify({
        "practice": practice,
        "provider": provider or "unknown",
        "target_lang": target_lang,
        "text_length": text_length,
        "text_type": text_type,
    })


# ──────────────────────────────────────────────────────────────
# API — Buscar vídeos
# ──────────────────────────────────────────────────────────────
@app.route("/api/videos", methods=["POST"])
def search_videos():
    data = _require_json_object()
    query = _normalize_text_field(
        data.get("query"),
        "Query",
        max_chars=MAX_QUERY_CHARS,
    )
    lang = _normalize_lang(data.get("lang"), default="en")

    videos, source, error = _search_youtube_videos(
        query,
        lang=lang,
        max_results=8,
        allow_generic_fallback=False,
    )
    if error and not videos:
        return jsonify({"error": error}), 500

    return jsonify({"videos": videos, "source": source})


# ──────────────────────────────────────────────────────────────
# API — YouTube Transcrição (Karaoke)
# ──────────────────────────────────────────────────────────────
@app.route("/api/youtube-transcript", methods=["POST"])
def youtube_transcript():
    data = _require_json_object()
    raw_video = (
        data.get("video")
        or data.get("url")
        or data.get("video_id")
        or ""
    )
    raw_video = _normalize_text_field(
        raw_video,
        "Vídeo",
        max_chars=320,
    )
    preferred_lang = _normalize_lang(data.get("preferred_lang"), default="en")
    timing_mode = _normalize_timing_mode(data.get("timing_mode"), default="balanced")

    video_id = _extract_youtube_video_id(raw_video)
    if not video_id:
        return jsonify({
            "error": "Não foi possível identificar o ID do vídeo. "
                     "Use um link válido do YouTube ou o ID de 11 caracteres."
        }), 400

    if YouTubeTranscriptApi is None and yt_dlp is None:
        return jsonify({
            "error": "Dependências ausentes: instale "
                     "'youtube-transcript-api' e/ou 'yt-dlp'."
        }), 500

    transcript, extract_errors = _extract_transcript_by_mode(
        video_id,
        preferred_lang,
        timing_mode,
    )

    if transcript is None:
        payload, status = _build_transcript_error_response(extract_errors)
        return jsonify(payload), status

    metadata = _fetch_youtube_oembed(video_id)

    host_origin = request.host_url.rstrip("/")
    return jsonify({
        "video_id": video_id,
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "embed_url": (
            f"https://www.youtube.com/embed/{video_id}"
            f"?enablejsapi=1&origin={host_origin}"
        ),
        "title": metadata.get("title", ""),
        "channel": metadata.get("author_name", ""),
        "thumbnail": (
            metadata.get("thumbnail_url")
            or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        ),
        "segments": transcript["segments"],
        "language_code": transcript["language_code"],
        "language": transcript["language"],
        "is_generated": transcript["is_generated"],
        "source": transcript.get("source", "unknown"),
        "timing_offset_sec": transcript.get("timing_offset_sec", 0.0),
        "timing_mode": timing_mode,
        "stats": transcript["stats"],
    })


# ──────────────────────────────────────────────────────────────
# API — YouTube Transcript Study (frase a frase)
# ──────────────────────────────────────────────────────────────
@app.route("/api/youtube-transcript-study", methods=["POST"])
def youtube_transcript_study():
    data = _require_json_object()
    preferred_lang = _normalize_lang(data.get("preferred_lang"), default="en")
    target_lang = _normalize_study_target_lang(data.get("target_lang"), default="pt")
    timing_mode = _normalize_timing_mode(data.get("timing_mode"), default="balanced")
    max_phrases = _coerce_int(
        data.get("max_phrases", MAX_STUDY_SEGMENTS),
        default=MAX_STUDY_SEGMENTS,
        min_value=4,
        max_value=32,
    )
    max_words = _coerce_int(
        data.get("max_words", MAX_STUDY_WORDS),
        default=MAX_STUDY_WORDS,
        min_value=2,
        max_value=10,
    )

    transcript = None
    metadata = {}
    video_id = ""

    raw_segments = data.get("segments")
    if isinstance(raw_segments, list) and raw_segments:
        segments = _normalize_input_transcript_segments(raw_segments)
        if not segments:
            return jsonify({"error": "Segmentos inválidos para estudo."}), 400
        source_lang = _normalize_lang(data.get("source_lang"), default=preferred_lang)
        word_count = sum(len(seg["text"].split()) for seg in segments)
        total_duration = max(seg["end"] for seg in segments)
        transcript = {
            "segments": segments,
            "language_code": source_lang,
            "language": source_lang,
            "is_generated": True,
            "source": str(data.get("source", "client_segments") or "client_segments"),
            "timing_offset_sec": _coerce_float(data.get("timing_offset_sec")) or 0.0,
            "stats": {
                "segments": len(segments),
                "words": word_count,
                "duration_sec": round(total_duration, 2),
            },
        }

        raw_video = (
            data.get("video")
            or data.get("url")
            or data.get("video_id")
            or ""
        )
        if str(raw_video or "").strip():
            video_id = _extract_youtube_video_id(str(raw_video))
            if video_id:
                metadata = _fetch_youtube_oembed(video_id)
    else:
        raw_video = (
            data.get("video")
            or data.get("url")
            or data.get("video_id")
            or ""
        )
        raw_video = _normalize_text_field(
            raw_video,
            "Vídeo",
            max_chars=320,
        )
        video_id = _extract_youtube_video_id(raw_video)
        if not video_id:
            return jsonify({
                "error": "Não foi possível identificar o ID do vídeo. "
                         "Use um link válido do YouTube ou o ID de 11 caracteres."
            }), 400

        if YouTubeTranscriptApi is None and yt_dlp is None:
            return jsonify({
                "error": "Dependências ausentes: instale "
                         "'youtube-transcript-api' e/ou 'yt-dlp'."
            }), 500

        transcript, extract_errors = _extract_transcript_by_mode(
            video_id,
            preferred_lang,
            timing_mode,
        )
        if transcript is None:
            payload, status = _build_transcript_error_response(extract_errors)
            return jsonify(payload), status
        metadata = _fetch_youtube_oembed(video_id)

    source_lang = transcript.get("language_code") or preferred_lang
    try:
        study = _build_youtube_transcript_study(
            transcript["segments"],
            source_lang=source_lang,
            target_lang=target_lang,
            max_segments=max_phrases,
            max_words_per_phrase=max_words,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    host_origin = request.host_url.rstrip("/")
    watch_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
    embed_url = (
        f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&origin={host_origin}"
        if video_id else ""
    )

    return jsonify({
        "study": {
            "video_id": video_id,
            "watch_url": watch_url,
            "embed_url": embed_url,
            "title": metadata.get("title", ""),
            "channel": metadata.get("author_name", ""),
            "source_transcript": transcript.get("source", "unknown"),
            "timing_mode": timing_mode,
            "timing_offset_sec": transcript.get("timing_offset_sec", 0.0),
            "source_language": source_lang,
            "target_language": target_lang,
            "ai_provider": study.get("ai_provider", "unknown"),
            "warning": study.get("warning", ""),
            "lesson_intro": study.get("lesson_intro", ""),
            "phrases": study["phrases"],
            "stats": {
                "phrases_analyzed": len(study["phrases"]),
                "segments_total": transcript.get("stats", {}).get("segments", len(transcript["segments"])),
                "words_total": transcript.get("stats", {}).get("words", 0),
            },
        }
    })


# ──────────────────────────────────────────────────────────────
# API — Progresso
# ──────────────────────────────────────────────────────────────
@app.route("/api/progress", methods=["GET"])
def get_progress():
    learner = _build_learner_context({}, default_lang=request.args.get("lang") or "en")
    adaptive_entries = _ADAPTIVE_STORE.get_progress_entries(learner)
    if adaptive_entries:
        return jsonify(adaptive_entries)
    with _DATA_LOCK:
        entries = _load_progress()
    return jsonify([_serialize_progress_entry(entry) for entry in entries])


@app.route("/api/progress", methods=["POST"])
def save_progress_entry():
    data = _require_json_object()
    learner = _build_learner_context(data, default_lang=data.get("lang") or "en")

    entry_date = _normalize_text_field(
        data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "Data",
        required=False,
        max_chars=20,
    ) or datetime.now().strftime("%Y-%m-%d")

    entry = {
        "date": entry_date,
        "material": _normalize_text_field(
            data.get("material", ""),
            "Material",
            required=False,
            max_chars=320,
        ),
        "duration_min": _coerce_int(
            data.get("duration_min", 0),
            default=0,
            min_value=0,
            max_value=720,
        ),
        "repetitions": _coerce_int(
            data.get("repetitions", 0),
            default=0,
            min_value=0,
            max_value=300,
        ),
        "difficulty": _coerce_int(
            data.get("difficulty", 3),
            default=3,
            min_value=1,
            max_value=5,
        ),
        "notes": _normalize_text_field(
            data.get("notes", ""),
            "Notas",
            required=False,
            max_chars=1000,
        ),
    }
    adaptive_saved = _ADAPTIVE_STORE.save_progress_entry(learner, entry)
    if adaptive_saved:
        with _DATA_LOCK:
            entries = _load_progress()
            entries.append(entry)
            _save_progress(entries)
        dashboard = _ADAPTIVE_STORE.get_dashboard(
            learner,
            fallback_lang=learner.target_lang,
        )
        return jsonify({
            "ok": True,
            "total": int(dashboard.get("summary", {}).get("sessions") or 0),
            "entry": adaptive_saved,
            "source": "postgres",
        })
    with _DATA_LOCK:
        entries = _load_progress()
        entries.append(entry)
        _save_progress(entries)
        total = len(entries)
    response = {"ok": True, "total": total, "source": "json"}
    if _ADAPTIVE_STORE.last_error:
        response["warning"] = _ADAPTIVE_STORE.last_error
    return jsonify(response)


@app.route("/api/progress/<int:index>", methods=["DELETE"])
def delete_progress_entry(index):
    learner = _build_learner_context({}, default_lang=request.args.get("lang") or "en")
    if _ADAPTIVE_STORE.delete_progress_entry(learner, index):
        total = len(_ADAPTIVE_STORE.get_progress_entries(learner))
        return jsonify({"ok": True, "total": total, "source": "postgres"})
    with _DATA_LOCK:
        entries = _load_progress()
        if 0 <= index < len(entries):
            entries.pop(index)
            _save_progress(entries)
            return jsonify({"ok": True, "total": len(entries)})
    return jsonify({"error": "Índice inválido."}), 404


@app.route("/api/progress/export", methods=["GET"])
def export_progress_csv():
    learner = _build_learner_context({}, default_lang=request.args.get("lang") or "en")
    entries = _ADAPTIVE_STORE.get_progress_entries(learner)
    if not entries:
        with _DATA_LOCK:
            entries = _load_progress()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Data", "Material", "Duração (min)", "Repetições", "Dificuldade", "Observações"]
    )
    for entry in entries:
        writer.writerow(
            [
                _safe_csv_cell(entry.get("date", "")),
                _safe_csv_cell(entry.get("material", "")),
                _coerce_int(entry.get("duration_min", 0), default=0, min_value=0, max_value=720),
                _coerce_int(entry.get("repetitions", 0), default=0, min_value=0, max_value=300),
                _coerce_int(entry.get("difficulty", 3), default=3, min_value=1, max_value=5),
                _safe_csv_cell(entry.get("notes", "")),
            ]
        )
    csv_content = output.getvalue()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=shadowing_progress.csv"},
    )


@app.route("/api/learner/dashboard", methods=["GET"])
def learner_dashboard():
    lang = request.args.get("lang") or "en"
    return jsonify(_adaptive_dashboard_for_request(default_lang=lang))


@app.route("/api/learner/review", methods=["POST"])
def learner_review_item():
    data = _require_json_object()
    if not _ADAPTIVE_STORE.enabled:
        return jsonify({"error": "Coach adaptativo indisponível no momento."}), 503

    item_id = _coerce_int(
        data.get("item_id", 0),
        default=0,
        min_value=0,
        max_value=2_000_000_000,
    )
    if item_id <= 0:
        return jsonify({"error": "item_id inválido."}), 400

    result_key = re.sub(r"\s+", "", str(data.get("result", "") or "")).strip().lower()
    score_map = {
        "again": 35,
        "hard": 60,
        "good": 88,
        "easy": 96,
    }
    raw_score = data.get("score")
    if raw_score in (None, ""):
        raw_score = score_map.get(result_key)
    if raw_score in (None, ""):
        return jsonify({"error": "Informe um resultado válido para a revisão."}), 400

    learner = _build_learner_context(
        data,
        default_lang=data.get("lang") or request.args.get("lang") or "en",
    )
    updated = _ADAPTIVE_STORE.review_item(
        learner,
        item_id=item_id,
        score=raw_score,
        notes=str(data.get("notes", "") or ""),
    )
    if not updated:
        message = _ADAPTIVE_STORE.last_error or "Item de revisão não encontrado."
        status = 404 if "não encontrado" in message.lower() else 400
        return jsonify({"error": message}), status

    dashboard = _ADAPTIVE_STORE.get_dashboard(
        learner,
        fallback_lang=learner.target_lang,
    )
    dashboard.setdefault("learner", {})
    dashboard.setdefault("summary", {})
    dashboard["adaptive_enabled"] = bool(_ADAPTIVE_STORE.enabled)
    if _ADAPTIVE_STORE.last_error:
        dashboard["adaptive_warning"] = _ADAPTIVE_STORE.last_error

    return jsonify({
        "ok": True,
        "item": updated,
        "dashboard": dashboard,
        "source": "postgres",
    })


# ──────────────────────────────────────────────────────────────
# API — Histórico de Sessões
# ──────────────────────────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
def get_history():
    with _DATA_LOCK:
        entries = _load_history()
    return jsonify(entries)


@app.route("/api/history", methods=["POST"])
def save_history_entry():
    data = _require_json_object()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": _normalize_text_field(
            data.get("text", ""),
            "Texto",
            required=False,
            max_chars=500,
        ),
        "language": _normalize_lang(data.get("language"), default="en"),
        "engine": _normalize_text_field(
            data.get("engine", "piper"),
            "Engine",
            required=False,
            max_chars=24,
        ) or "piper",
    }
    with _DATA_LOCK:
        entries = _load_history()
        # Avoid exact duplicates
        if not entries or entries[-1].get("text") != entry["text"]:
            entries.append(entry)
            _save_history(entries)
    return jsonify({"ok": True})


# ──────────────────────────────────────────────────────────────
# API — Limpeza e Stats
# ──────────────────────────────────────────────────────────────
@app.route("/api/audio-stats", methods=["GET"])
def audio_stats():
    return jsonify(_get_audio_stats())


@app.route("/api/cleanup", methods=["POST"])
def cleanup_audio():
    removed = _cleanup_old_audio(max_age_hours=0)  # Remove tudo
    return jsonify({"removed": removed, "stats": _get_audio_stats()})


# ──────────────────────────────────────────────────────────────
# API — Conversação por Voz
# ──────────────────────────────────────────────────────────────
@app.route("/api/conversation", methods=["POST"])
def voice_conversation():
    data = _require_json_object()
    audio_b64 = str(data.get("audio_b64", "")).strip()
    lang = _normalize_lang(data.get("lang"), default="en")
    learner = _build_learner_context(data, default_lang=lang)
    voice = _normalize_text_field(
        data.get("voice", "leah"), "Voz", required=False, max_chars=48
    ) or "leah"
    history = _normalize_conversation_history(data.get("history", []))
    requested_tts_engine = _normalize_tts_engine(
        data.get("tts_engine"),
        use_lmnt=data.get("use_lmnt"),
        default="lmnt",
    )
    piper_options = _build_piper_request_options(
        data,
        default_context_hint="conversation_reply",
        default_profile="chat",
    )
    suggest  = _coerce_bool(data.get("suggest", False), default=False)

    if not audio_b64:
        return jsonify({"error": "Áudio não fornecido."}), 400

    if not (WhisperModel and LOCAL_WHISPER_ENABLED):
        return jsonify({
            "error": "Whisper local não disponível. Instale 'faster-whisper' e reinicie."
        }), 500

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return jsonify({"error": "Áudio inválido (base64 corrompido)."}), 400

    audio_id = str(uuid.uuid4())[:8]
    tmp_audio_path = AUDIO_DIR / f"conv_in_{audio_id}.webm"
    tmp_audio_path.write_bytes(audio_bytes)

    try:
        # 1. Transcrição local com Whisper
        model = _get_local_whisper_model()
        lang_code = lang.split("-")[0]
        seg_iter, _ = model.transcribe(
            str(tmp_audio_path),
            language=lang_code,
            beam_size=5,
            best_of=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        user_text = " ".join(seg.text.strip() for seg in seg_iter).strip()

        if not user_text:
            return jsonify({
                "error": "Não consegui entender o áudio. Fale mais próximo ao microfone."
            }), 400

        # 2. Resposta da IA (com continuidade local sem token)
        lang_label = PRACTICE_LANG_LABELS.get(lang, lang.upper())
        system_prompt = (
            f"You are Alex, a real person — a native {lang_label} speaker in your late 20s. "
            f"You are chatting casually with a Brazilian friend who wants to practice {lang_label}.\n\n"
            "Your personality:\n"
            "- Curious, witty, warm. You genuinely enjoy conversations.\n"
            "- You share brief personal opinions, reactions, and anecdotes when relevant.\n"
            "- You ask ONE follow-up question per reply to keep the conversation going.\n"
            "- You react naturally: surprise, humor, agreement, curiosity.\n\n"
            "Hard rules:\n"
            f"- Write ONLY in {lang_label}. Never use Portuguese or any other language.\n"
            "- NEVER mention that you are an AI, a language model, a practice tool, or an assistant.\n"
            "- NEVER say phrases like 'I am here to help', 'I am your partner', 'keep practicing'.\n"
            "- NEVER repeat a phrase you already used in this conversation.\n"
            "- Keep each reply to 2-3 short sentences maximum — like a real chat message.\n"
            "- No emojis. No bullet points. Plain natural speech only.\n"
            "- If the user makes a grammar mistake, just respond naturally — do NOT correct them.\n"
            "- If the user says something unclear or odd, react to it curiously, like a real person would."
        )

        ctx_lines = []
        for m in (history[-10:] if len(history) > 10 else history):
            role_label = "Alex" if m.get("role") == "assistant" else "Friend"
            ctx_lines.append(f"{role_label}: {m.get('content', '')}")
        context_str = "\n".join(ctx_lines)
        user_msg = f"{context_str}\nFriend: {user_text}\nAlex:" if context_str else f"Friend: {user_text}\nAlex:"

        ai_text = None
        provider = None
        warning = ""
        if has_text_ai_provider():
            ai_text, provider = chat_with_fallback(
                system_prompt,
                user_msg,
                max_tokens=200,
                temperature=0.85,
            )

        if not ai_text:
            ai_text = _build_local_conversation_reply(user_text, lang, history or [])
            provider = "fallback_local"
            warning = (
                "IA textual indisponivel no momento. "
                "Resposta local basica ativada."
            )

        ai_text = ai_text.strip()
        ai_text_tts = _strip_emojis(ai_text)  # texto limpo só para o TTS

        # 3. TTS da resposta
        audio_filename = ""
        tts_engine = ""
        out_audio_bytes = None
        piper_meta = None

        if requested_tts_engine == "lmnt":
            if LMNT_API_KEY:
                out_audio_bytes = lmnt_synthesize(ai_text_tts, voice=voice, lang=lang)
            if not out_audio_bytes:
                out_audio_bytes = deepgram_synthesize(ai_text_tts, lang=lang)
                if out_audio_bytes:
                    tts_engine = "deepgram"
        elif requested_tts_engine == "deepgram":
            out_audio_bytes = deepgram_synthesize(ai_text_tts, lang=lang)
            if not out_audio_bytes and LMNT_API_KEY:
                out_audio_bytes = lmnt_synthesize(ai_text_tts, voice=voice, lang=lang)
                if out_audio_bytes:
                    tts_engine = "lmnt"
        else:
            # local/piper only
            out_audio_bytes = None

        if out_audio_bytes:
            audio_filename = f"conv_out_{audio_id}.mp3"
            (AUDIO_DIR / audio_filename).write_bytes(out_audio_bytes)
            if not tts_engine:
                tts_engine = requested_tts_engine if requested_tts_engine in {"lmnt", "deepgram"} else "lmnt"
        if not audio_filename:
            wav_filename = f"conv_out_{audio_id}.wav"
            wav_path = AUDIO_DIR / wav_filename
            piper_result = piper_synthesize_to_file(
                ai_text_tts,
                wav_path,
                lang=lang,
                request_options=piper_options,
            )
            if piper_result.get("ok"):
                audio_filename = wav_filename
                tts_engine = "piper"
                piper_meta = _public_piper_meta(piper_result)

        result = {
            "user_text": user_text,
            "ai_text": ai_text,
            "provider": provider or "unknown",
            "tts_engine": tts_engine,
        }
        if piper_meta:
            result["piper_meta"] = piper_meta
        if warning:
            result["warning"] = warning
        if audio_filename:
            result["audio_url"] = url_for("static", filename=f"audio/{audio_filename}")

        # 4. Sugestões de resposta (colinha)
        if suggest:
            suggestion_history = list(history or [])
            suggestion_history.append({"role": "user", "content": user_text})
            result["suggestions"] = _conversation_generate_reply_suggestions(
                suggestion_history,
                lang,
                latest_ai_text=ai_text,
                limit=3,
                force_local=(provider == "fallback_local"),
            )

        _ADAPTIVE_STORE.record_conversation_turn(
            learner,
            user_text=user_text,
            ai_text=ai_text,
            history_size=len(history or []),
        )

        return jsonify(result)

    finally:
        try:
            tmp_audio_path.unlink(missing_ok=True)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
# API — Conversation Lesson
# ──────────────────────────────────────────────────────────────
def _normalize_conversation_role(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"assistant", "ai", "alex", "teacher", "bot", "system", "speaker2"}:
        return "ai"
    if raw in {"user", "student", "friend", "aluno", "human", "speaker1"}:
        return "user"
    return "user"


def _normalize_conversation_history(history) -> list[dict]:
    if not isinstance(history, list):
        return []

    normalized = []
    for item in history:
        if not isinstance(item, dict):
            continue
        content = _clean_caption_text(item.get("content") or item.get("text") or "")
        if not content:
            continue
        normalized.append({
            "role": _normalize_conversation_role(item.get("role")),
            "content": content,
        })
    return normalized[-24:]


def _normalize_lesson_transcript(raw_transcript, history: list[dict]) -> list[dict]:
    transcript = []
    if isinstance(raw_transcript, list):
        for item in raw_transcript:
            if not isinstance(item, dict):
                continue
            original = _clean_caption_text(
                item.get("original")
                or item.get("text")
                or item.get("content")
                or ""
            )
            if not original:
                continue
            transcript.append({
                "role": _normalize_conversation_role(
                    item.get("role") or item.get("speaker") or item.get("from")
                ),
                "original": original,
                "translation": _clean_caption_text(
                    item.get("translation")
                    or item.get("translated")
                    or item.get("meaning")
                    or ""
                ),
            })

    if not transcript:
        for item in history:
            transcript.append({
                "role": _normalize_conversation_role(item.get("role")),
                "original": _clean_caption_text(item.get("content") or ""),
                "translation": "",
            })

    return transcript[:40]


def _normalize_lesson_vocabulary(raw_items) -> list[dict]:
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("words") or []
    if not isinstance(raw_items, list):
        return []

    items = []
    seen = set()
    for item in raw_items:
        if isinstance(item, str):
            word = _clean_caption_text(item)
            meaning = ""
            example = ""
        elif isinstance(item, dict):
            word = _clean_caption_text(
                item.get("word")
                or item.get("term")
                or item.get("expression")
                or ""
            )
            meaning = _clean_caption_text(
                item.get("meaning")
                or item.get("translation")
                or item.get("definition")
                or ""
            )
            example = _clean_caption_text(
                item.get("example")
                or item.get("usage")
                or ""
            )
        else:
            continue

        if not word:
            continue
        key = word.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append({
            "word": word,
            "meaning": meaning,
            "example": example,
        })
        if len(items) >= 8:
            break
    return items


def _normalize_lesson_grammar(raw_items) -> list[dict]:
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("points") or []
    if not isinstance(raw_items, list):
        return []

    items = []
    for item in raw_items:
        if isinstance(item, str):
            point = _clean_caption_text(item)
            explanation = ""
            example = ""
        elif isinstance(item, dict):
            point = _clean_caption_text(
                item.get("point")
                or item.get("topic")
                or item.get("title")
                or ""
            )
            explanation = _clean_caption_text(
                item.get("explanation")
                or item.get("description")
                or item.get("meaning")
                or ""
            )
            example = _clean_caption_text(
                item.get("example")
                or item.get("usage")
                or ""
            )
        else:
            continue

        if not point:
            continue
        items.append({
            "point": point,
            "explanation": explanation,
            "example": example,
        })
        if len(items) >= 6:
            break
    return items


def _normalize_lesson_corrections(raw_items) -> list[dict]:
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("mistakes") or []
    if not isinstance(raw_items, list):
        return []

    items = []
    for item in raw_items:
        if isinstance(item, dict):
            original = _clean_caption_text(
                item.get("original")
                or item.get("wrong")
                or item.get("mistake")
                or ""
            )
            corrected = _clean_caption_text(
                item.get("corrected")
                or item.get("right")
                or item.get("fix")
                or ""
            )
            tip = _clean_caption_text(
                item.get("tip")
                or item.get("explanation")
                or item.get("note")
                or ""
            )
            if not original and not corrected:
                continue
            items.append({
                "original": original,
                "corrected": corrected,
                "tip": tip,
            })
        elif isinstance(item, str):
            tip = _clean_caption_text(item)
            if tip:
                items.append({
                    "original": "",
                    "corrected": "",
                    "tip": tip,
                })

        if len(items) >= 8:
            break
    return items


def _normalize_lesson_tips(raw_tips) -> list[str]:
    if raw_tips is None:
        return []

    values = []
    if isinstance(raw_tips, str):
        values = [raw_tips]
    elif isinstance(raw_tips, list):
        values = raw_tips
    else:
        return []

    tips = []
    seen = set()
    for item in values:
        if isinstance(item, dict):
            text = _clean_caption_text(item.get("tip") or item.get("text") or "")
            pieces = [text] if text else []
        else:
            text = _clean_caption_text(item)
            if not text:
                pieces = []
            else:
                pieces = [part.strip() for part in re.split(r"[;\n]+", text) if part.strip()]

        for piece in pieces:
            key = piece.casefold()
            if key in seen:
                continue
            seen.add(key)
            tips.append(piece)
            if len(tips) >= 6:
                return tips
    return tips


def _resolve_smart_conversation_lesson_focus(history: list[dict],
                                             source_lang: str,
                                             translate_to: str) -> tuple[str, str]:
    src_base = str(source_lang or "").split("-")[0].lower()
    tgt_base = str(translate_to or "").split("-")[0].lower()
    pt_mode = tgt_base == "pt"

    user_rows = [
        _clean_caption_text(item.get("content", ""))
        for item in (history or [])
        if isinstance(item, dict) and _normalize_conversation_role(item.get("role")) == "user"
    ]
    user_rows = [row for row in user_rows if row]
    if not user_rows:
        reason = (
            "Foco automatico equilibrado: ainda ha pouco conteudo do aluno para especializar a aula."
            if pt_mode else
            "Balanced auto focus: there is not enough student content yet for specialization."
        )
        return "balanced", reason

    joined = " ".join(user_rows)
    tokens = [_analysis_word_key(token) for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", joined)]
    tokens = [token for token in tokens if token]
    unique_ratio = (len(set(tokens)) / max(1, len(tokens))) if tokens else 0.0

    repetition_hits = sum(
        1 for row in user_rows
        if re.search(r"\b(\w+)(\s+\1\b)+", row, flags=re.IGNORECASE)
    )
    fragmented_hits = sum(
        1 for row in user_rows
        if (
            row.count(",") >= 2
            or (
                len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", row)) >= 14
                and not re.search(r"[.!?]$", row)
            )
        )
    )
    question_structure_hits = sum(
        1 for row in user_rows
        if re.search(
            r"\bwhat do you favorite\b|\bwhat('?s| is) the rules\b|\bwhat about you do you\b",
            row.casefold(),
        )
    )

    mixed_language_hits = 0
    if src_base == "en":
        foreign_markers = {
            "nao", "não", "mas", "porque", "aliás", "alias", "espanol", "español",
            "frances", "francais", "futuri", "pass", "spinole",
        }
        for row in user_rows:
            row_fold = row.casefold()
            marker_count = sum(
                1 for marker in foreign_markers
                if re.search(rf"\b{re.escape(marker)}\b", row_fold)
            )
            has_accents = bool(re.search(r"[À-ÖØ-öø-ÿ]", row))
            if marker_count >= 1 or has_accents:
                mixed_language_hits += 1

    correction_score = (
        (repetition_hits * 2)
        + (fragmented_hits * 2)
        + (question_structure_hits * 2)
        + mixed_language_hits
    )
    vocabulary_score = 0
    if len(tokens) >= 20 and unique_ratio < 0.48:
        vocabulary_score += 2
    elif len(tokens) >= 12 and unique_ratio < 0.58:
        vocabulary_score += 1
    if len(set(tokens)) < 10:
        vocabulary_score += 1

    if correction_score >= 3:
        reason = (
            "Foco automatico em correcoes: detectei frases fragmentadas e estruturas para ajustar nas ultimas falas."
            if pt_mode else
            "Auto focus on corrections: I detected fragmented phrases and structures to improve in recent turns."
        )
        return "corrections", reason

    if vocabulary_score >= 2:
        reason = (
            "Foco automatico em vocabulario: houve repeticao de palavras e vale ampliar o repertorio ativo."
            if pt_mode else
            "Auto focus on vocabulary: repeated wording suggests it is a good moment to expand active vocabulary."
        )
        return "vocabulary", reason

    reason = (
        "Foco automatico equilibrado: conversa variada, com ajustes leves de vocabulario e estrutura."
        if pt_mode else
        "Balanced auto focus: the conversation is varied, with light vocabulary and structure improvements."
    )
    return "balanced", reason


def _conversation_lesson_attempt_json_repair(raw_response: str,
                                             conv_text: str,
                                             lang_label: str,
                                             translate_label: str,
                                             lesson_focus: str) -> dict | None:
    cleaned_raw = _clean_caption_text(raw_response or "")
    if not cleaned_raw or not has_text_ai_provider():
        return None

    system = (
        "You are a strict JSON formatter for language-learning payloads. "
        "Return ONLY valid JSON with no markdown or extra text."
    )
    prompt = (
        f"Conversation in {lang_label}:\n{conv_text}\n\n"
        f"Requested focus: {lesson_focus}\n\n"
        "Malformed model output to repair:\n"
        f"{cleaned_raw}\n\n"
        "Return EXACT JSON:\n"
        '{"transcript":[{"role":"user or ai","original":"...","translation":"..."}],'
        '"lesson":{"summary":"...","vocabulary":[{"word":"...","meaning":"...","example":"..."}],'
        '"grammar":[{"point":"...","explanation":"...","example":"..."}],'
        '"corrections":[{"original":"...","corrected":"...","tip":"..."}],'
        '"tips":["...","..."]}}\n\n'
        "Rules:\n"
        f"- summary, grammar explanations, correction tips, and vocabulary meaning must be in {translate_label}\n"
        "- transcript role must be only 'user' or 'ai'\n"
        "- keep concise, useful content and avoid placeholders.\n"
        "Return only JSON."
    )
    repaired_raw, _ = chat_with_fallback(
        system,
        prompt,
        max_tokens=2200,
        temperature=0.2,
    )
    if not repaired_raw:
        return None
    return _extract_json_payload_from_text(repaired_raw or "")


def _conversation_lesson_ai_corrections(transcript: list[dict],
                                        translate_to: str,
                                        source_lang: str,
                                        limit: int = 6) -> list[dict]:
    if not has_text_ai_provider():
        return []
    src_base = str(source_lang or "").split("-")[0].lower()
    if src_base != "en":
        return []

    user_rows = [
        _clean_caption_text(item.get("original", ""))
        for item in (transcript or [])
        if isinstance(item, dict) and item.get("role") == "user"
    ]
    user_rows = [row for row in user_rows if row]
    if not user_rows:
        return []

    target_label = PRACTICE_LANG_LABELS.get(translate_to, translate_to.upper())
    enumerated = [f"{idx + 1}. {row}" for idx, row in enumerate(user_rows[-10:])]
    system = (
        "You are an English speaking coach. "
        "Return only valid JSON."
    )
    prompt = (
        "Student utterances:\n"
        + "\n".join(enumerated)
        + "\n\nReturn JSON with format:\n"
        '{"corrections":[{"original":"...","corrected":"...","tip":"..."}]}\n\n'
        f"Rules:\n"
        f"- tip must be in {target_label}\n"
        "- keep original exactly as said by student\n"
        "- corrected must be a natural English sentence preserving intent\n"
        "- include 3 to 8 corrections for the most relevant mistakes\n"
        "- skip uncertain noise instead of hallucinating.\n"
        "Return only JSON."
    )
    raw, _ = chat_with_fallback(system, prompt, max_tokens=900, temperature=0.2)
    parsed = _extract_json_payload_from_text(raw or "") if raw else None
    if not parsed:
        return []

    corrected = _normalize_lesson_corrections(
        (parsed.get("corrections") if isinstance(parsed, dict) else None)
        or (parsed.get("lesson", {}) or {}).get("corrections")
    )
    return corrected[:max(1, int(limit or 1))]


def _conversation_lesson_default_summary(translate_to: str, turns: int) -> str:
    templates = {
        "pt": "Resumo automático da sua conversa ({turns} falas). Revise o vocabulário e repita em voz alta.",
        "en": "Auto summary of your conversation ({turns} turns). Review the vocabulary and practice aloud.",
        "es": "Resumen automático de tu conversación ({turns} intervenciones). Revisa el vocabulario y practica en voz alta.",
        "fr": "Resume automatique de votre conversation ({turns} tours). Revisez le vocabulaire et pratiquez a voix haute.",
        "de": "Automatische Zusammenfassung Ihres Gesprachs ({turns} Beitrage). Wiederholen Sie den Wortschatz laut.",
        "it": "Riepilogo automatico della tua conversazione ({turns} battute). Ripassa il vocabolario e parla ad alta voce.",
    }
    template = templates.get(translate_to, templates["en"])
    return template.format(turns=max(1, int(turns or 0)))


def _conversation_lesson_contextual_summary(transcript: list[dict], translate_to: str) -> str:
    turns = len(transcript or [])
    base = " ".join(item.get("original", "") for item in (transcript or [])).casefold()
    if not base:
        return _conversation_lesson_default_summary(translate_to, turns)

    topic_checks = {
        "routine": ("morning", "day", "today", "plans", "routine"),
        "coffee": ("coffee", "cafe"),
        "learning": ("english", "shadowing", "study", "learn", "practice"),
        "entertainment": ("movie", "movies", "show", "series", "witcher", "watch"),
    }
    found = [name for name, hints in topic_checks.items() if any(h in base for h in hints)]

    if not found:
        return _conversation_lesson_default_summary(translate_to, turns)

    labels = {
        "pt": {
            "routine": "rotina e planos do dia",
            "coffee": "cafe e rotina da manha",
            "learning": "aprendizado de ingles com shadowing",
            "entertainment": "series e filmes",
        },
        "en": {
            "routine": "daily routine and plans",
            "coffee": "coffee and morning routine",
            "learning": "learning English with shadowing",
            "entertainment": "shows and movies",
        },
    }
    chosen = labels.get(translate_to, labels["en"])
    topics = [chosen[key] for key in found[:3] if key in chosen]
    if not topics:
        return _conversation_lesson_default_summary(translate_to, turns)

    if translate_to == "pt":
        return (
            f"Vocês conversaram sobre {', '.join(topics)}. "
            "Revise as falas principais e repita em voz alta com ritmo natural."
        )
    return (
        f"You discussed {', '.join(topics)}. "
        "Review key turns and repeat them aloud with natural rhythm."
    )


def _conversation_lesson_default_tips(translate_to: str) -> list[str]:
    tips_map = {
        "pt": [
            "Repita cada fala em voz alta, focando no ritmo natural.",
            "Escolha 3 palavras novas e use em frases suas.",
            "Grave 30 segundos de resposta e compare com a IA.",
        ],
        "en": [
            "Repeat each turn aloud and focus on natural rhythm.",
            "Pick 3 new words and use them in your own sentences.",
            "Record a 30-second reply and compare with the AI voice.",
        ],
        "es": [
            "Repite cada turno en voz alta con ritmo natural.",
            "Elige 3 palabras nuevas y usalas en frases tuyas.",
            "Graba una respuesta de 30 segundos y comparala con la IA.",
        ],
        "fr": [
            "Repetez chaque reponse a voix haute avec un rythme naturel.",
            "Choisissez 3 mots nouveaux et utilisez-les dans vos phrases.",
            "Enregistrez 30 secondes de reponse et comparez avec l'IA.",
        ],
        "de": [
            "Wiederholen Sie jeden Satz laut und mit naturlichem Rhythmus.",
            "Wahlen Sie 3 neue Worter und bilden Sie eigene Satze.",
            "Nehmen Sie 30 Sekunden auf und vergleichen Sie mit der KI.",
        ],
        "it": [
            "Ripeti ogni battuta ad alta voce con ritmo naturale.",
            "Scegli 3 parole nuove e usale in frasi tue.",
            "Registra 30 secondi di risposta e confrontali con l'IA.",
        ],
    }
    return tips_map.get(translate_to, tips_map["en"])


def _conversation_user_rows_from_transcript(transcript: list[dict]) -> list[str]:
    rows = []
    for item in transcript or []:
        if not isinstance(item, dict):
            continue
        if _normalize_conversation_role(item.get("role")) != "user":
            continue
        text = _clean_caption_text(
            item.get("original")
            or item.get("content")
            or item.get("text")
            or ""
        )
        if text:
            rows.append(text)
    return rows


def _conversation_lesson_fallback_pronunciation_feedback(transcript: list[dict],
                                                         translate_to: str,
                                                         source_lang: str,
                                                         corrections: list[dict] | None = None) -> dict:
    src_base = str(source_lang or "").split("-")[0].lower()
    tgt_base = str(translate_to or "").split("-")[0].lower()
    pt_mode = tgt_base == "pt"

    user_rows = _conversation_user_rows_from_transcript(transcript)
    if not user_rows:
        return {
            "score": 72,
            "level": (
                "Base inicial (estimada)"
                if pt_mode else
                "Starting baseline (estimated)"
            ),
            "summary": (
                "Ainda ha pouco audio transcrito para avaliar pronuncia com consistencia."
                if pt_mode else
                "There is not enough transcribed speech yet to assess pronunciation consistently."
            ),
            "tips": (
                [
                    "Continue conversando por mais alguns turnos para obter uma avaliacao melhor.",
                    "Fale em blocos curtos e mantenha ritmo estavel.",
                ]
                if pt_mode else
                [
                    "Keep talking for a few more turns to get a better estimate.",
                    "Speak in short chunks and keep a steady rhythm.",
                ]
            ),
            "drill_phrases": [],
        }

    joined = " ".join(user_rows)
    words = [
        _analysis_word_key(token)
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", joined)
    ]
    words = [token for token in words if token]

    repetition_hits = sum(
        1
        for row in user_rows
        if re.search(r"\b(\w+)(\s+\1\b)+", row, flags=re.IGNORECASE)
    )
    fragmented_hits = sum(
        1
        for row in user_rows
        if (
            row.count(",") >= 2
            or (
                len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", row)) >= 14
                and not re.search(r"[.!?]$", row)
            )
        )
    )
    filler_hits = sum(
        len(re.findall(r"\b(uh+|um+|er+|ah+|hmm|tipo)\b", row.casefold()))
        for row in user_rows
    )
    mixed_language_hits = 0
    if src_base == "en":
        foreign_markers = {
            "nao", "não", "mas", "porque", "alias", "aliás",
            "espanol", "español", "frances", "francais",
        }
        for row in user_rows:
            row_fold = row.casefold()
            marker_count = sum(
                1
                for marker in foreign_markers
                if re.search(rf"\b{re.escape(marker)}\b", row_fold)
            )
            has_accents = bool(re.search(r"[À-ÖØ-öø-ÿ]", row))
            if marker_count >= 1 or has_accents:
                mixed_language_hits += 1

    correction_count = len(corrections or [])
    penalty = (
        (repetition_hits * 4)
        + (fragmented_hits * 3)
        + min(6, filler_hits)
        + (mixed_language_hits * 3)
        + min(10, correction_count * 2)
    )
    bonus = min(8, max(0, len(words) // 18))
    score = max(48, min(96, 84 + bonus - penalty))

    if pt_mode:
        if score >= 82:
            level = "Muito boa para o nivel atual"
        elif score >= 68:
            level = "Boa, com pontos de ajuste"
        else:
            level = "Em desenvolvimento"
    else:
        if score >= 82:
            level = "Strong for your current level"
        elif score >= 68:
            level = "Good, with adjustment points"
        else:
            level = "Developing"

    findings = []
    if repetition_hits:
        findings.append(
            "repeticoes no inicio de frases"
            if pt_mode else
            "repetitions at sentence starts"
        )
    if fragmented_hits:
        findings.append(
            "frases longas com quebras"
            if pt_mode else
            "long fragmented sentences"
        )
    if mixed_language_hits:
        findings.append(
            "mistura de idiomas em alguns trechos"
            if pt_mode else
            "language mixing in a few turns"
        )
    if not findings:
        findings.append(
            "ritmo geral consistente"
            if pt_mode else
            "overall rhythm is consistent"
        )

    summary = (
        "Avaliacao estimada pela transcricao (sem analise acustica detalhada): "
        + ", ".join(findings[:3])
        + "."
        if pt_mode else
        "Estimated from transcript (without detailed acoustic analysis): "
        + ", ".join(findings[:3])
        + "."
    )

    tips = []
    seen_tips = set()
    for item in corrections or []:
        tip = _clean_caption_text(item.get("tip") or "")
        key = tip.casefold()
        if not tip or key in seen_tips:
            continue
        seen_tips.add(key)
        tips.append(tip)
        if len(tips) >= 2:
            break

    generic_tips = (
        [
            "Fale em blocos curtos de 5-8 palavras antes de acelerar.",
            "Realce a silaba tonica das palavras principais.",
            "Conecte palavras frequentes sem pausas longas entre elas.",
            "Se travar, pause e recomece sem repetir o inicio da frase.",
        ]
        if pt_mode else
        [
            "Speak in short 5-8 word chunks before speeding up.",
            "Stress the key content words in each sentence.",
            "Link frequent word pairs without long pauses.",
            "If you get stuck, pause and restart without repeating the beginning.",
        ]
    )
    for tip in generic_tips:
        key = tip.casefold()
        if key in seen_tips:
            continue
        seen_tips.add(key)
        tips.append(tip)
        if len(tips) >= 5:
            break

    drills = []
    seen_drills = set()
    for row in reversed(user_rows[-5:]):
        sample = row
        row_words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", row)
        if len(row_words) > 12:
            simplified = _build_simplified_feedback_sentence(row)
            if simplified:
                sample = simplified
        sample = _clean_caption_text(sample)
        sample_words = sample.split()
        if len(sample_words) < 3:
            continue
        if len(sample_words) > 12:
            sample = " ".join(sample_words[:12]).strip()
        key = sample.casefold()
        if not key or key in seen_drills:
            continue
        seen_drills.add(key)
        drills.append(sample)
        if len(drills) >= 3:
            break

    if not drills:
        for item in corrections or []:
            sample = _clean_caption_text(item.get("corrected") or item.get("original") or "")
            if not sample:
                continue
            key = sample.casefold()
            if key in seen_drills:
                continue
            seen_drills.add(key)
            drills.append(sample)
            if len(drills) >= 3:
                break

    if not drills:
        drills = _local_conversation_suggestions(source_lang)[:2]

    return {
        "score": score,
        "level": level,
        "summary": summary,
        "tips": tips[:5],
        "drill_phrases": drills[:3],
    }


def _normalize_conversation_pronunciation_feedback(raw_feedback,
                                                   transcript: list[dict],
                                                   translate_to: str,
                                                   source_lang: str,
                                                   corrections: list[dict] | None = None) -> dict:
    fallback = _conversation_lesson_fallback_pronunciation_feedback(
        transcript,
        translate_to=translate_to,
        source_lang=source_lang,
        corrections=corrections,
    )
    if not isinstance(raw_feedback, dict):
        return fallback

    score = _coerce_int(
        raw_feedback.get("score"),
        default=fallback.get("score", 72),
        min_value=1,
        max_value=100,
    )
    level = _clean_caption_text(
        raw_feedback.get("level")
        or raw_feedback.get("band")
        or raw_feedback.get("rating")
        or ""
    ) or fallback.get("level", "")
    summary = _clean_caption_text(
        raw_feedback.get("summary")
        or raw_feedback.get("analysis")
        or raw_feedback.get("note")
        or ""
    ) or fallback.get("summary", "")

    tips = _normalize_lesson_tips(
        raw_feedback.get("tips")
        or raw_feedback.get("advice")
        or raw_feedback.get("recommendations")
    )
    if not tips:
        tips = fallback.get("tips", [])
    tips = tips[:5]

    drills = _normalize_conversation_suggestions(
        raw_feedback.get("drill_phrases")
        or raw_feedback.get("drills")
        or raw_feedback.get("practice_phrases")
        or [],
        limit=3,
    )
    if not drills:
        drills = fallback.get("drill_phrases", [])

    return {
        "score": score,
        "level": level,
        "summary": summary,
        "tips": tips,
        "drill_phrases": drills[:3],
    }


def _conversation_lesson_fallback_vocabulary(transcript: list[dict],
                                             translate_to: str,
                                             limit: int = 5) -> list[dict]:
    user_text = " ".join(
        item.get("original", "")
        for item in transcript
        if isinstance(item, dict) and item.get("role") == "user"
    )
    all_text = " ".join(item.get("original", "") for item in transcript)
    transcript_sentences = [
        _clean_caption_text(item.get("original", ""))
        for item in (transcript or [])
        if _clean_caption_text(item.get("original", ""))
    ]
    words = _extract_keyword_fallback_words(user_text, limit=max(1, limit) * 2)
    if len(words) < max(1, limit):
        extra = _extract_keyword_fallback_words(all_text, limit=max(1, limit) * 3)
        seen = {_analysis_word_key(word) for word in words}
        for word in extra:
            key = _analysis_word_key(word)
            if not key or key in seen:
                continue
            seen.add(key)
            words.append(word)
            if len(words) >= max(1, limit):
                break
    meanings = {
        "pt": "Termo usado na conversa.",
        "en": "Word used in the conversation.",
        "es": "Termino usado en la conversacion.",
        "fr": "Terme utilise dans la conversation.",
        "de": "Begriff aus dem Gesprach.",
        "it": "Termine usato nella conversazione.",
    }
    meaning = meanings.get(translate_to, meanings["en"])
    enriched = []
    for word in words[:max(1, limit)]:
        word_key = _analysis_word_key(word)
        example = _analysis_find_sentence_for_word(transcript_sentences, word_key)
        if translate_to == "pt":
            approx = _local_translate_fallback_text(word, source_lang="en", target_lang="pt")
            if approx and approx.casefold() != word.casefold():
                current_meaning = f"{approx} (aprox.)"
            else:
                current_meaning = meaning
        else:
            current_meaning = meaning
        enriched.append({
            "word": word,
            "meaning": current_meaning,
            "example": example,
        })
    return enriched[:max(1, limit)]


def _build_simplified_feedback_sentence(text: str) -> str:
    cleaned = _clean_caption_text(text or "")
    if not cleaned:
        return ""
    cleaned = re.sub(
        r"\b(i[' ]?m sorry|repeat please|by the way|you know|i mean|well|actually|sorry|first)\b[,\s]*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,")
    pieces = [
        part.strip(" ,")
        for part in re.split(r"[,.!?;]+", cleaned)
        if part.strip(" ,")
    ]
    if not pieces:
        pieces = [cleaned]
    selected = []
    for piece in pieces:
        words = piece.split()
        if len(words) < 3:
            continue
        if len(words) > 11:
            piece = " ".join(words[:11]).strip()
        piece = piece[:1].upper() + piece[1:] if piece else piece
        selected.append(piece)
        if len(selected) >= 2:
            break
    if not selected:
        for piece in pieces:
            words = piece.split()
            if len(words) < 2:
                continue
            if len(words) > 9:
                piece = " ".join(words[:9]).strip()
            piece = piece[:1].upper() + piece[1:] if piece else piece
            selected.append(piece)
            if len(selected) >= 2:
                break
    if not selected:
        return ""
    sentence = ". ".join(selected).strip()
    sentence = re.sub(r"\b(i\s+\w+)\s+i\b", r"\1. I", sentence, flags=re.IGNORECASE)
    if len(sentence.split()) < 4:
        return ""
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence


def _conversation_lesson_fallback_corrections(transcript: list[dict],
                                              translate_to: str,
                                              source_lang: str,
                                              limit: int = 6,
                                              allow_generic: bool = False) -> list[dict]:
    rows = [
        _clean_caption_text(item.get("original", ""))
        for item in (transcript or [])
        if isinstance(item, dict) and item.get("role") == "user"
    ]
    if not rows:
        return []

    src_base = str(source_lang or "").split("-")[0].lower()
    pt_mode = str(translate_to or "").split("-")[0].lower() == "pt"

    corrections = []
    seen = set()

    def _append(original: str, corrected: str, tip_pt: str, tip_en: str):
        original_clean = _clean_caption_text(original or "")
        corrected_clean = _clean_caption_text(corrected or "")
        key = f"{original_clean}|{corrected_clean}".casefold()
        if key in seen:
            return
        seen.add(key)
        corrections.append({
            "original": original_clean,
            "corrected": corrected_clean,
            "tip": tip_pt if pt_mode else tip_en,
        })

    english_rules = (
        (
            r"\bit's a going\b",
            "It's going",
            "Use 'It's going', sem 'a' antes de verbo em -ing.",
            "Use 'It's going' without 'a' before an -ing verb.",
        ),
        (
            r"\bhave you watching\b",
            "Have you been watching",
            "Para continuidade, prefira 'Have you been watching...'.",
            "For ongoing actions, prefer 'Have you been watching...'.",
        ),
        (
            r"\bin the study english\b",
            "studying English",
            "Forma natural: 'I am studying English'.",
            "Natural form: 'I am studying English'.",
        ),
        (
            r"\band this moment\b",
            "right now",
            "Para tempo presente, prefira 'right now' ou 'at this moment'.",
            "For present-time context, prefer 'right now' or 'at this moment'.",
        ),
        (
            r"\bi eat apple\b",
            "I'm eating an apple",
            "Para ação acontecendo agora, use present continuous: 'I'm eating...'.",
            "For an action happening now, use present continuous: 'I'm eating...'.",
        ),
        (
            r"\bwhat do you favorite fruit\b",
            "What is your favorite fruit",
            "Em perguntas com 'favorite', use 'What is your favorite...?'",
            "For 'favorite' questions, use 'What is your favorite...?'",
        ),
        (
            r"\bi don't say bacon at home\b",
            "I don't bake at home",
            "Aqui o natural seria 'I don't bake at home'.",
            "The natural phrasing here is 'I don't bake at home'.",
        ),
        (
            r"\bi usually and guanabara\b",
            "I usually go to Guanabara",
            "Faltou verbo de movimento: 'I usually go to...'.",
            "A movement verb is missing: 'I usually go to...'.",
        ),
        (
            r"\bi like you grill\b",
            "I like grilling",
            "Depois de 'like', prefira 'grilling' para ideia geral.",
            "After 'like', prefer 'grilling' for general preference.",
        ),
        (
            r"\bmy\s+fox\s+(in|is)\s+(the\s+)?english\b",
            "my focus is English",
            "Use 'focus' (nao 'fox') e mantenha 'is': 'My focus is English'.",
            "Use 'focus' (not 'fox') and keep the verb: 'My focus is English'.",
        ),
        (
            r"\bi\s+write\s+in\s+france\s+the\s+verbs\b",
            "I write the verbs in French",
            "Para idioma, use 'in French': 'I write the verbs in French'.",
            "For language reference, use 'in French': 'I write the verbs in French'.",
        ),
        (
            r"\bwhat('?s| is)\s+the\s+rules\b",
            "What are the rules",
            "Em plural, pergunte 'What are the rules?'.",
            "With plural noun, ask 'What are the rules?'.",
        ),
        (
            r"\bi\s+say\s+english\s+my\s+favorite\b",
            "English is my favorite language",
            "Forma natural: 'English is my favorite language.'",
            "Natural form: 'English is my favorite language.'",
        ),
        (
            r"\bwhat\s+about\s+you\s+do\s+you\b",
            "What about you? Do you",
            "Separe a pergunta em duas partes: 'What about you? Do you...?'",
            "Split it into two parts: 'What about you? Do you...?'",
        ),
        (
            r"\bi don't remember the battery we've been talking about\b",
            "I don't remember what we were talking about",
            "Aqui 'battery' parece ruido; use 'what we were talking about'.",
            "Here 'battery' seems like noise; use 'what we were talking about'.",
        ),
        (
            r"\bfor questions?,?\s+see you\b",
            "I have no more questions. See you",
            "Fechamento mais natural: 'I have no more questions. See you.'",
            "More natural closing: 'I have no more questions. See you.'",
        ),
    )

    for text in rows:
        if len(corrections) >= limit:
            break
        if not text:
            continue

        row_start_count = len(corrections)
        lower = text.casefold()

        # Remove repetição imediata de palavras (comum em STT espontâneo).
        deduped = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
        deduped = re.sub(r"\s{2,}", " ", deduped).strip()
        if deduped != text:
            _append(
                text,
                deduped,
                "Evite repetir a mesma palavra duas vezes seguidas.",
                "Avoid repeating the same word twice in a row.",
            )

        if len(corrections) >= limit:
            break

        if src_base == "en":
            for pattern, replacement, tip_pt, tip_en in english_rules:
                if len(corrections) >= limit:
                    break
                if not re.search(pattern, lower, flags=re.IGNORECASE):
                    continue
                corrected = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if corrected.casefold() == text.casefold():
                    continue
                _append(text, corrected, tip_pt, tip_en)
                if (len(corrections) - row_start_count) >= 2:
                    break

            if len(corrections) >= limit:
                break

            word_count = len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text))
            if (
                len(corrections) == row_start_count
                and
                word_count >= 14
                and text.count(",") >= 2
                and len(corrections) < limit
            ):
                simplified = _build_simplified_feedback_sentence(text)
                if simplified and simplified.casefold() != text.casefold():
                    _append(
                        text,
                        simplified,
                        "Frase longa e fragmentada: divida em 1-2 frases curtas com sujeito + verbo.",
                        "Long fragmented phrase: split it into 1-2 short sentences with clear subject + verb.",
                    )

            if len(corrections) >= limit:
                break

            if (
                len(corrections) == row_start_count
                and re.search(r"\bdifficulting\b|\bfuturi\b|\bcontinues\b", lower)
            ):
                simplified = _build_simplified_feedback_sentence(text)
                _append(
                    text,
                    simplified or "It is difficult to build formal sentences, so I start with present tense.",
                    "Organize a ideia com tempo verbal claro (presente, passado, futuro).",
                    "Organize the idea with a clear tense choice (present, past, future).",
                )

    if corrections:
        return corrections[:limit]

    ai_corrections = _conversation_lesson_ai_corrections(
        transcript,
        translate_to=translate_to,
        source_lang=source_lang,
        limit=limit,
    )
    if ai_corrections:
        return ai_corrections[:limit]

    if not allow_generic:
        return []

    generic_tip = (
        "Nao foi possivel fechar correcoes especificas com alta confianca. Foque em frases curtas, verbo principal claro e perguntas com auxiliar (do/does/is/are)."
        if pt_mode else
        "No high-confidence specific correction was found. Focus on short sentences, one main verb, and auxiliary verbs in questions."
    )
    return [{
        "original": "",
        "corrected": "",
        "tip": generic_tip,
    }]


def _conversation_lesson_fallback_grammar(transcript: list[dict],
                                          translate_to: str,
                                          source_lang: str,
                                          corrections: list[dict] | None = None,
                                          limit: int = 4) -> list[dict]:
    src_base = str(source_lang or "").split("-")[0].lower()
    pt_mode = str(translate_to or "").split("-")[0].lower() == "pt"
    rows = [
        _clean_caption_text(item.get("original", ""))
        for item in (transcript or [])
        if isinstance(item, dict) and item.get("role") == "user"
    ]
    if not rows:
        return []

    points = []
    seen = set()

    def _add(point_pt: str, point_en: str, expl_pt: str, expl_en: str, example: str):
        point = point_pt if pt_mode else point_en
        key = point.casefold()
        if key in seen:
            return
        seen.add(key)
        points.append({
            "point": point,
            "explanation": expl_pt if pt_mode else expl_en,
            "example": example,
        })

    if src_base == "en":
        joined = " ".join(rows).casefold()
        if re.search(r"\bi eat\b.*\b(now|right now|moment)\b|\bi eat apple\b", joined):
            _add(
                "Present continuous para ações do momento",
                "Present continuous for actions happening now",
                "Quando a ação acontece agora, prefira 'I am + verbo-ing'.",
                "When the action is happening now, prefer 'I am + verb-ing'.",
                "I'm eating an apple right now.",
            )
        if "what do you favorite" in joined or "what do you favorite fruit" in joined:
            _add(
                "Estrutura de perguntas com 'favorite'",
                "Question structure with 'favorite'",
                "Use 'What is your favorite...?' em vez de 'What do you favorite...?'",
                "Use 'What is your favorite...?' instead of 'What do you favorite...?'",
                "What is your favorite fruit?",
            )
        if re.search(r"\beat apple\b|\ba favorite supermarket\b", joined):
            _add(
                "Artigos em inglês (a/an/the)",
                "Articles in English (a/an/the)",
                "Evite substantivo singular sem artigo quando necessário.",
                "Avoid singular nouns without an article when needed.",
                "I'm eating an apple.",
            )
        if re.search(r"\bi like i like\b|\bdo do you\b", joined):
            _add(
                "Fluidez: evitar repetições",
                "Fluency: avoid repeated chunks",
                "Ao falar, tente pausar em vez de repetir o início da frase.",
                "When speaking, pause instead of repeating the sentence start.",
                "Do you have any big plans?",
            )

    if corrections:
        for corr in corrections[:max(1, limit)]:
            tip = _clean_caption_text(corr.get("tip", ""))
            if not tip:
                continue
            _add(
                "Ponto de atenção da correção",
                "Correction focus point",
                tip,
                tip,
                _clean_caption_text(corr.get("corrected") or corr.get("original") or ""),
            )
            if len(points) >= limit:
                break

    return points[:limit]


def _normalize_conversation_lesson_payload(parsed,
                                           history: list[dict],
                                           translate_to: str,
                                           source_lang: str = "en",
                                           lesson_focus: str = "balanced") -> dict:
    payload = parsed if isinstance(parsed, dict) else {}

    raw_transcript = payload.get("transcript")
    if not isinstance(raw_transcript, list):
        for key in ("conversation", "dialogue", "turns", "messages"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                raw_transcript = candidate
                break

    lesson_root = payload.get("lesson")
    if not isinstance(lesson_root, dict):
        lesson_root = payload

    summary = _clean_caption_text(
        lesson_root.get("summary")
        or lesson_root.get("overview")
        or payload.get("summary")
        or ""
    )
    vocabulary = _normalize_lesson_vocabulary(
        lesson_root.get("vocabulary")
        or lesson_root.get("vocab")
        or payload.get("vocabulary")
        or payload.get("vocab")
    )
    grammar = _normalize_lesson_grammar(
        lesson_root.get("grammar")
        or lesson_root.get("grammar_points")
        or payload.get("grammar")
        or payload.get("grammar_points")
    )
    corrections = _normalize_lesson_corrections(
        lesson_root.get("corrections")
        or lesson_root.get("mistakes")
        or payload.get("corrections")
        or payload.get("mistakes")
    )

    tips_source = lesson_root.get("tips")
    if tips_source in (None, ""):
        tips_source = payload.get("tips")
    tips = _normalize_lesson_tips(tips_source)

    focus = _normalize_lesson_focus(lesson_focus, default="balanced")
    if focus == "smart":
        focus = "balanced"
    transcript = _normalize_lesson_transcript(raw_transcript, history)
    if not summary:
        summary = _conversation_lesson_contextual_summary(transcript, translate_to)
    if not vocabulary:
        vocab_limit = 7 if focus == "vocabulary" else 5
        vocabulary = _conversation_lesson_fallback_vocabulary(
            transcript,
            translate_to,
            limit=vocab_limit,
        )
    if not corrections:
        corr_limit = 7 if focus == "corrections" else (2 if focus == "vocabulary" else 4)
        corrections = _conversation_lesson_fallback_corrections(
            transcript,
            translate_to,
            source_lang=source_lang,
            limit=corr_limit,
            allow_generic=(focus == "corrections"),
        )
    if not grammar:
        grammar_limit = 5 if focus == "corrections" else 3
        grammar = _conversation_lesson_fallback_grammar(
            transcript,
            translate_to,
            source_lang=source_lang,
            corrections=corrections,
            limit=grammar_limit,
        )
    if not tips:
        tips = _conversation_lesson_default_tips(translate_to)
    if focus == "corrections":
        extra_tip = (
            "Priorize corrigir suas ultimas frases: fale mais devagar e confirme cada estrutura."
            if translate_to == "pt" else
            "Prioritize fixing your latest phrases: speak slower and validate each structure."
        )
        if extra_tip not in tips:
            tips = [extra_tip] + tips
            tips = tips[:6]

    suggestion_history = []
    for row in transcript:
        if not isinstance(row, dict):
            continue
        role = _normalize_conversation_role(row.get("role"))
        text = _clean_caption_text(row.get("original") or "")
        if not text:
            continue
        suggestion_history.append({
            "role": role,
            "content": text,
        })
    if not suggestion_history:
        suggestion_history = history

    raw_suggestions = (
        payload.get("next_reply_suggestions")
        or payload.get("suggestions")
        or lesson_root.get("next_reply_suggestions")
        or lesson_root.get("suggestions")
    )
    next_reply_suggestions = _normalize_conversation_suggestions(raw_suggestions, limit=4)
    if not next_reply_suggestions:
        next_reply_suggestions = _conversation_generate_reply_suggestions(
            suggestion_history,
            source_lang,
            limit=4,
        )

    raw_pronunciation_feedback = (
        payload.get("pronunciation_feedback")
        or lesson_root.get("pronunciation_feedback")
    )
    pronunciation_feedback = _normalize_conversation_pronunciation_feedback(
        raw_pronunciation_feedback,
        transcript,
        translate_to=translate_to,
        source_lang=source_lang,
        corrections=corrections,
    )

    return {
        "transcript": transcript,
        "lesson": {
            "summary": summary,
            "vocabulary": vocabulary,
            "grammar": grammar,
            "corrections": corrections,
            "tips": tips,
        },
        "next_reply_suggestions": next_reply_suggestions,
        "pronunciation_feedback": pronunciation_feedback,
        "lesson_focus": focus,
    }


def _conversation_translation_unavailable_label(target_lang: str) -> str:
    labels = {
        "pt": "Tradução indisponível.",
        "en": "Translation unavailable.",
        "es": "Traducción no disponible.",
        "fr": "Traduction indisponible.",
        "de": "Ubersetzung nicht verfugbar.",
        "it": "Traduzione non disponibile.",
    }
    return labels.get(target_lang, labels["en"])


EN_PT_FALLBACK_PHRASES = (
    (r"\bgood morning\b", "bom dia"),
    (r"\bgood night\b", "boa noite"),
    (r"\bhow are you\b", "como voce esta"),
    (r"\bhow's your day\b", "como esta seu dia"),
    (r"\bhow's your day starting off\b", "como seu dia esta comecando"),
    (r"\bhow is your day starting off\b", "como seu dia esta comecando"),
    (r"\bwhat are your plans for today\b", "quais sao seus planos para hoje"),
    (r"\bwhat about your morning so far\b", "como foi sua manha ate agora"),
    (r"\bdo you have any big plans\b", "voce tem grandes planos"),
    (r"\bwhat about you\b", "e voce"),
    (r"\bno worries\b", "sem problemas"),
    (r"\bsee you later\b", "ate mais tarde"),
    (r"\bthank you\b", "obrigado"),
    (r"\bthanks\b", "obrigado"),
    (r"\bby the way\b", "a proposito"),
)

EN_PT_FALLBACK_WORDS = {
    "hello": "ola",
    "hi": "oi",
    "hey": "oi",
    "good": "bom",
    "morning": "manha",
    "day": "dia",
    "starting": "comecando",
    "off": "agora",
    "it": "isso",
    "is": "e",
    "going": "indo",
    "pretty": "bem",
    "well": "bem",
    "thanks": "obrigado",
    "for": "por",
    "asking": "perguntar",
    "how": "como",
    "about": "sobre",
    "your": "seu",
    "my": "meu",
    "so": "tao",
    "far": "ate agora",
    "plans": "planos",
    "today": "hoje",
    "some": "alguns",
    "coffee": "cafe",
    "life": "vida",
    "saver": "salvador",
    "do": "fazer",
    "you": "voce",
    "have": "tem",
    "any": "algum",
    "big": "grandes",
    "fun": "diversao",
    "relaxing": "relaxando",
    "watching": "assistindo",
    "show": "serie",
    "movie": "filme",
    "favorite": "favorito",
    "line": "frase",
    "later": "mais tarde",
    "bye": "tchau",
    "no": "nao",
    "worries": "problema",
    "talk": "falar",
    "to": "para",
    "a": "um",
    "one": "um",
}


def _local_translate_en_to_pt(text: str) -> str:
    working = _clean_caption_text(text or "")
    if not working:
        return ""

    translated = working
    for pattern, repl in EN_PT_FALLBACK_PHRASES:
        translated = re.sub(pattern, repl, translated, flags=re.IGNORECASE)

    tokens = re.findall(r"[A-Za-z']+|\d+|\s+|[^\w\s]", translated, flags=re.UNICODE)
    out = []
    for token in tokens:
        if not token:
            continue
        if token.isspace() or re.fullmatch(r"[^\w\s]", token, flags=re.UNICODE):
            out.append(token)
            continue
        key = token.casefold()
        mapped = EN_PT_FALLBACK_WORDS.get(key)
        if not mapped:
            out.append(token)
            continue
        if token[:1].isupper():
            mapped = mapped[:1].upper() + mapped[1:]
        out.append(mapped)

    final_text = "".join(out)
    final_text = re.sub(r"\s+([,.;!?])", r"\1", final_text)
    final_text = re.sub(r"\s{2,}", " ", final_text).strip()
    return final_text or working


def _local_translate_fallback_text(text: str, source_lang: str, target_lang: str) -> str:
    src_base = str(source_lang or "").split("-")[0].lower()
    tgt_base = str(target_lang or "").split("-")[0].lower()
    original = _clean_caption_text(text or "")
    if not original:
        return ""
    if src_base == tgt_base:
        return original
    if src_base == "en" and tgt_base == "pt":
        return _local_translate_en_to_pt(original)
    return ""


def _backfill_conversation_transcript_translations(transcript: list[dict],
                                                   source_lang: str,
                                                   target_lang: str) -> list[dict]:
    if not isinstance(transcript, list):
        return []

    src_base = str(source_lang or "").split("-")[0].lower()
    tgt_base = str(target_lang or "").split("-")[0].lower()

    normalized = []
    for item in transcript:
        if not isinstance(item, dict):
            continue
        original = _clean_caption_text(
            item.get("original")
            or item.get("text")
            or item.get("content")
            or ""
        )
        if not original:
            continue
        normalized.append({
            "role": _normalize_conversation_role(item.get("role")),
            "original": original,
            "translation": _clean_caption_text(item.get("translation") or ""),
        })

    if not normalized:
        return []

    if src_base == tgt_base:
        for row in normalized:
            if not row.get("translation"):
                row["translation"] = row["original"]
        return normalized

    missing = [
        {"phrase_index": idx, "text": row["original"]}
        for idx, row in enumerate(normalized)
        if not row.get("translation")
    ]

    if missing and has_text_ai_provider():
        filled = {}
        batch_size = 8
        for start in range(0, len(missing), batch_size):
            chunk = missing[start:start + batch_size]
            chunk_filled = _backfill_study_translation_pronunciation(
                chunk,
                source_lang=source_lang,
                target_lang=target_lang,
            )
            if chunk_filled:
                filled.update(chunk_filled)
        for item in missing:
            idx = item["phrase_index"]
            if idx < 0 or idx >= len(normalized):
                continue
            translated = _clean_caption_text(
                (filled.get(idx) or {}).get("translation") or ""
            )
            if translated:
                normalized[idx]["translation"] = translated

    fallback_label = _conversation_translation_unavailable_label(tgt_base)
    for row in normalized:
        if not row.get("translation"):
            local_translation = _local_translate_fallback_text(
                row.get("original", ""),
                source_lang=source_lang,
                target_lang=target_lang,
            )
            row["translation"] = local_translation or fallback_label

    return normalized


@app.route("/api/conversation/lesson", methods=["POST"])
def api_conversation_lesson():
    data = _require_json_object()
    history = _normalize_conversation_history(data.get("history", []))
    lang = _normalize_lang(data.get("lang"), default="en")
    learner = _build_learner_context(data, default_lang=lang)
    translate_to = _normalize_study_target_lang(data.get("translate_to"), default="pt")
    lesson_focus_requested = _normalize_lesson_focus(data.get("lesson_focus"), default="smart")

    if not history:
        return jsonify({"error": "Sem histórico de conversa"}), 400

    lesson_focus = lesson_focus_requested
    lesson_focus_reason = ""
    if lesson_focus_requested == "smart":
        lesson_focus, lesson_focus_reason = _resolve_smart_conversation_lesson_focus(
            history,
            source_lang=lang,
            translate_to=translate_to,
        )
    if lesson_focus not in {"balanced", "corrections", "vocabulary"}:
        lesson_focus = "balanced"

    lang_label      = PRACTICE_LANG_LABELS.get(lang, lang.upper())
    translate_label = PRACTICE_LANG_LABELS.get(translate_to, translate_to.upper())
    focus_labels = {
        "balanced": "balanced",
        "corrections": "corrections-heavy",
        "vocabulary": "vocabulary-heavy",
    }
    focus_label = focus_labels.get(lesson_focus, "balanced")

    if lesson_focus == "corrections":
        focus_instruction = (
            f"- prioritize corrections: provide 4-8 correction items in {translate_label}\n"
            "- each correction must reference an exact student utterance from transcript\n"
            f"- grammar: 3-5 items in {translate_label}\n"
            f"- vocabulary: 2-4 items only, concise in {translate_label}\n"
            "- avoid generic placeholders such as 'no clear error'\n"
            "- in transcript, preserve each turn and provide clear translation"
        )
    elif lesson_focus == "vocabulary":
        focus_instruction = (
            f"- prioritize vocabulary: provide 6-10 vocabulary items in {translate_label}\n"
            f"- grammar: 1-3 items in {translate_label}\n"
            f"- corrections: up to 3 key mistakes in {translate_label}\n"
            "- in transcript, preserve each turn and provide clear translation"
        )
    else:
        focus_instruction = (
            f"- vocabulary: 3-6 notable words/phrases, meanings in {translate_label}\n"
            f"- grammar: 2-4 grammar points in {translate_label}\n"
            f"- corrections: important mistakes in {translate_label}\n"
            "- in transcript, preserve each turn and provide clear translation"
        )

    formatted_lines = []
    for msg in history:
        speaker = "Student" if msg.get("role") == "user" else "Alex"
        formatted_lines.append(f"{speaker}: {msg.get('content', '')}")
    conv_text = "\n".join(formatted_lines)

    system = (
        f"You are an expert {lang_label} language teacher for Brazilian students. "
        "Analyze a conversation and produce a structured lesson. "
        "Return ONLY a valid JSON object — no markdown, no code block, no explanation."
    )
    prompt = (
        f"Conversation in {lang_label}:\n{conv_text}\n\n"
        f"Lesson focus mode: {focus_label}\n\n"
        "Return a JSON object with EXACTLY this structure:\n"
        '{"transcript":[{"role":"user or ai","original":"...","translation":"..."}],'
        '"lesson":{"summary":"...","vocabulary":[{"word":"...","meaning":"...","example":"..."}],'
        '"grammar":[{"point":"...","explanation":"...","example":"..."}],'
        '"corrections":[{"original":"...","corrected":"...","tip":"..."}],'
        '"tips":["...","..."]},'
        '"next_reply_suggestions":["...","...","..."],'
        '"pronunciation_feedback":{"score":1-100,"level":"...","summary":"...","tips":["..."],"drill_phrases":["..."]}}\n\n'
        f"Rules:\n"
        f"- transcript: one entry per turn; role is 'user' or 'ai'; "
        f"  original = the {lang_label} text as spoken; translation = {translate_label}\n"
        f"- summary: 1-2 sentences in {translate_label} describing what was discussed\n"
        f"{focus_instruction}\n"
        f"- tips: 2-3 practical tips in {translate_label} for the student\n"
        f"- next_reply_suggestions: exactly 3 short options in {lang_label} for what the student can say next\n"
        f"- pronunciation_feedback: score 1-100 + level + summary + tips in {translate_label}; "
        "estimate from transcript only (do not claim acoustic precision)\n"
        "- drill_phrases: 2-3 short phrases from the student transcript in original language for repetition drills\n"
        "Return ONLY the JSON. No markdown. No code fences."
    )

    try:
        if not has_text_ai_provider():
            fallback = _normalize_conversation_lesson_payload(
                {},
                history,
                translate_to,
                source_lang=lang,
                lesson_focus=lesson_focus,
            )
            fallback["transcript"] = _backfill_conversation_transcript_translations(
                fallback.get("transcript", []),
                source_lang=lang,
                target_lang=translate_to,
            )
            fallback["ai_provider"] = "fallback"
            fallback["lesson_focus"] = lesson_focus
            fallback["lesson_focus_requested"] = lesson_focus_requested
            if lesson_focus_reason:
                fallback["lesson_focus_reason"] = lesson_focus_reason
            fallback["warning"] = (
                "Nenhum provedor de IA textual disponível. "
                "A aula foi montada por análise local da conversa."
            )
            _ADAPTIVE_STORE.record_conversation_lesson(
                learner,
                lesson_payload=fallback,
            )
            return jsonify(fallback)

        raw, provider = chat_with_fallback(system, prompt, max_tokens=2500, temperature=0.35)
        parsed = _extract_json_payload_from_text(raw or "") if raw else None
        repaired = False
        if not parsed and raw:
            parsed = _conversation_lesson_attempt_json_repair(
                raw,
                conv_text=conv_text,
                lang_label=lang_label,
                translate_label=translate_label,
                lesson_focus=focus_label,
            )
            repaired = bool(parsed)

        response = _normalize_conversation_lesson_payload(
            parsed or {},
            history,
            translate_to,
            source_lang=lang,
            lesson_focus=lesson_focus,
        )
        response["transcript"] = _backfill_conversation_transcript_translations(
            response.get("transcript", []),
            source_lang=lang,
            target_lang=translate_to,
        )
        response["lesson_focus"] = lesson_focus
        response["lesson_focus_requested"] = lesson_focus_requested
        if lesson_focus_reason:
            response["lesson_focus_reason"] = lesson_focus_reason
        response["ai_provider"] = provider or "fallback"
        if not parsed:
            response["warning"] = (
                "A IA respondeu fora do formato esperado. "
                "Aplicamos normalização inteligente da conversa para montar a aula."
            )
        elif repaired:
            response["warning"] = (
                "A resposta da IA precisou de reestruturação automática, "
                "mas a aula foi preservada com foco completo."
            )
        _ADAPTIVE_STORE.record_conversation_lesson(
            learner,
            lesson_payload=response,
        )
        return jsonify(response)
    except Exception as e:
        app.logger.error("api_conversation_lesson error: %s", e, exc_info=True)
        fallback = _normalize_conversation_lesson_payload(
            {},
            history,
            translate_to,
            source_lang=lang,
            lesson_focus=lesson_focus,
        )
        fallback["transcript"] = _backfill_conversation_transcript_translations(
            fallback.get("transcript", []),
            source_lang=lang,
            target_lang=translate_to,
        )
        fallback["lesson_focus"] = lesson_focus
        fallback["lesson_focus_requested"] = lesson_focus_requested
        if lesson_focus_reason:
            fallback["lesson_focus_reason"] = lesson_focus_reason
        fallback["ai_provider"] = "fallback"
        fallback["warning"] = (
            "Falha temporária ao gerar a aula com IA. "
            "A aula foi montada por análise local da conversa."
        )
        _ADAPTIVE_STORE.record_conversation_lesson(
            learner,
            lesson_payload=fallback,
        )
        return jsonify(fallback)


# ──────────────────────────────────────────────────────────────
# API — Agent Orchestrator
# ──────────────────────────────────────────────────────────────
def _agent_internal_api_call(method: str, path: str, payload: dict | None = None) -> ToolResult:
    method_up = str(method or "POST").strip().upper()
    if method_up not in {"GET", "POST", "DELETE"}:
        return ToolResult(
            ok=False,
            status_code=500,
            error=f"Unsupported internal method '{method_up}' for path '{path}'.",
        )

    payload = payload or {}
    with app.test_client() as client:
        request_kwargs = {}
        if method_up == "GET":
            if payload:
                request_kwargs["query_string"] = payload
        else:
            request_kwargs["json"] = payload
        response = client.open(path, method=method_up, **request_kwargs)

    parsed = None
    try:
        parsed = response.get_json(silent=True)
    except Exception:
        parsed = None
    if parsed is None:
        raw_text = ""
        try:
            raw_text = response.get_data(as_text=True)
        except Exception:
            raw_text = ""
        parsed = {"raw": raw_text}

    ok = response.status_code < 400
    error = ""
    if not ok:
        if isinstance(parsed, dict):
            error = _clean_caption_text(parsed.get("error") or parsed.get("message") or "")
        if not error:
            error = f"HTTP {response.status_code} while calling {path}"

    return ToolResult(
        ok=ok,
        status_code=response.status_code,
        data=parsed,
        error=error,
    )


def _build_agent_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register("generate_session", lambda payload: _agent_internal_api_call("POST", "/api/generate", payload))
    registry.register("analyze_text", lambda payload: _agent_internal_api_call("POST", "/api/analyze", payload))
    registry.register("generate_practice_text", lambda payload: _agent_internal_api_call("POST", "/api/generate-practice", payload))
    registry.register("youtube_transcript", lambda payload: _agent_internal_api_call("POST", "/api/youtube-transcript", payload))
    registry.register("youtube_transcript_study", lambda payload: _agent_internal_api_call("POST", "/api/youtube-transcript-study", payload))
    registry.register("conversation_turn", lambda payload: _agent_internal_api_call("POST", "/api/conversation", payload))
    registry.register("conversation_lesson", lambda payload: _agent_internal_api_call("POST", "/api/conversation/lesson", payload))
    registry.register("progress_get", lambda payload: _agent_internal_api_call("GET", "/api/progress", payload))
    registry.register("progress_save", lambda payload: _agent_internal_api_call("POST", "/api/progress", payload))
    registry.register("history_get", lambda payload: _agent_internal_api_call("GET", "/api/history", payload))
    registry.register("status_get", lambda payload: _agent_internal_api_call("GET", "/api/status", payload))
    registry.register("audio_stats", lambda payload: _agent_internal_api_call("GET", "/api/audio-stats", payload))
    registry.register("cleanup_audio", lambda payload: _agent_internal_api_call("POST", "/api/cleanup", payload))

    return registry


def _get_agent_orchestrator() -> AgentOrchestrator:
    global _AGENT_ORCHESTRATOR
    if _AGENT_ORCHESTRATOR is None:
        _AGENT_ORCHESTRATOR = AgentOrchestrator(_build_agent_tool_registry())
    return _AGENT_ORCHESTRATOR


@app.route("/api/agent/intents", methods=["GET"])
def api_agent_intents():
    return jsonify({
        "default_intent": "auto",
        "intents": [
            {"name": "auto", "description": "Resolve o melhor agente por query/payload."},
            {"name": "practice", "description": "Geração de sessão, análise e texto de prática."},
            {"name": "conversation", "description": "Conversa por voz e aula da conversa."},
            {"name": "youtube", "description": "Transcrição e estudo frase a frase."},
            {"name": "progress", "description": "Resumo e registro de progresso."},
        ],
    })


@app.route("/api/agent/run", methods=["POST"])
def api_agent_run():
    data = _require_json_object()

    intent = str(data.get("intent", "auto") or "auto").strip().lower() or "auto"
    query = _clean_caption_text(data.get("query") or "")

    raw_payload = data.get("payload")
    if raw_payload is None:
        payload = {
            key: value
            for key, value in data.items()
            if key not in {"intent", "query", "payload"}
        }
    elif isinstance(raw_payload, dict):
        payload = raw_payload
    else:
        return jsonify({"error": "Campo 'payload' deve ser um objeto JSON."}), 400

    orchestrator = _get_agent_orchestrator()
    result = orchestrator.run(
        intent=intent,
        query=query,
        payload=payload,
    )
    return jsonify(result)


# ──────────────────────────────────────────────────────────────
# API — Status
# ──────────────────────────────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def api_status():
    ollama_model = _resolve_ollama_model()
    if _ADAPTIVE_STORE.enabled and not _ADAPTIVE_STORE.health().get("schema_ready"):
        _ADAPTIVE_STORE.ensure_schema()
    return jsonify({
        "lmnt": bool(LMNT_API_KEY),
        "piper": piper_available(),
        "piper_langs": piper_supported_languages(),
        "deepseek": bool(DEEPSEEK_API_KEY),
        "openrouter": bool(OPENROUTER_API_KEY),
        "openai_chat": bool(OPENAI_API_KEY),
        "ollama": bool(ollama_model),
        "ollama_model": ollama_model,
        "ai_text": bool(DEEPSEEK_API_KEY or OPENROUTER_API_KEY or OPENAI_API_KEY or ollama_model),
        "deepgram": bool(DEEPGRAM_API_KEY and DEEPGRAM_ENABLED),
        "deepgram_tts_langs": deepgram_tts_supported_languages(),
        "youtube_transcript": bool(YouTubeTranscriptApi),
        "yt_dlp": bool(yt_dlp),
        "local_whisper": bool(WhisperModel and LOCAL_WHISPER_ENABLED),
        "openai_transcribe": bool(OPENAI_API_KEY),
        "adaptive_learning": _ADAPTIVE_STORE.health(),
    })


# ══════════════════════════════════════════════════════════════
# WhatsApp Mini-Lesson Routes
# ══════════════════════════════════════════════════════════════

def _wa_strip_data_uri(value: str) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return "", ""
    if raw.startswith("data:") and "," in raw:
        header, data = raw.split(",", 1)
        mime = header[5:].split(";")[0].strip().lower()
        return data.strip(), mime
    return raw, ""


def _wa_extract_media_base64(payload) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []

    def _visit(node, depth: int = 0) -> None:
        if depth > 5:
            return
        if isinstance(node, str):
            stripped, mime = _wa_strip_data_uri(node)
            if stripped and len(stripped) > 80:
                candidates.append((stripped, mime))
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_lc = str(key).lower()
                if isinstance(value, str):
                    if (
                        key_lc in {"base64", "media", "file", "audio", "data"}
                        or "base64" in key_lc
                    ):
                        stripped, mime = _wa_strip_data_uri(value)
                        if stripped:
                            candidates.append((stripped, mime))
                elif isinstance(value, (dict, list)):
                    _visit(value, depth + 1)
            return
        if isinstance(node, list):
            for item in node[:10]:
                _visit(item, depth + 1)

    _visit(payload)
    if not candidates:
        return "", ""

    for data, mime in candidates:
        compact = re.sub(r"\s+", "", data)
        if len(compact) >= 120:
            return compact, mime
    return candidates[0]


def _wa_guess_audio_suffix(mime_type: str) -> str:
    mime = (mime_type or "").strip().lower()
    if "ogg" in mime or "opus" in mime:
        return ".ogg"
    if "mpeg" in mime or "mp3" in mime:
        return ".mp3"
    if "wav" in mime:
        return ".wav"
    if "aac" in mime:
        return ".aac"
    if "mp4" in mime or "m4a" in mime:
        return ".m4a"
    if "webm" in mime:
        return ".webm"
    return ".ogg"


def _wa_audio_bytes_to_ogg_b64(audio_bytes: bytes, *, input_suffix: str = ".mp3") -> str | None:
    if not audio_bytes:
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="wa_tts_") as tmp:
            tmp_dir = Path(tmp)
            in_path = tmp_dir / f"in{input_suffix}"
            out_path = tmp_dir / "out.ogg"
            in_path.write_bytes(audio_bytes)

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(in_path),
                    "-c:a", "libopus",
                    "-b:a", "64k",
                    "-ar", "48000",
                    str(out_path),
                ],
                capture_output=True,
                check=True,
                timeout=40,
            )
            return base64.b64encode(out_path.read_bytes()).decode()
    except Exception as exc:
        print(f"[WA TTS] Conversão para OGG falhou: {exc}")
        return None


def _wa_ai_tts_audio_b64(*, text: str = "", lang: str = "en") -> dict[str, Any] | None:
    cleaned = _strip_emojis(_clean_caption_text(text or ""))
    if not cleaned:
        return None
    cleaned = cleaned[:5000]

    normalized_lang = str(lang or "en").strip().lower().split("-")[0] or "en"
    mode = str(os.getenv("WHATSAPP_TTS_ENGINE", "auto") or "auto").strip().lower()
    if mode not in {"auto", "deepgram", "lmnt", "piper"}:
        mode = "auto"

    if mode in {"auto", "deepgram"}:
        dg_bytes = deepgram_synthesize(cleaned, lang=normalized_lang)
        dg_b64 = _wa_audio_bytes_to_ogg_b64(dg_bytes or b"", input_suffix=".mp3")
        if dg_b64:
            return {"audio_b64": dg_b64, "engine": "deepgram"}

    if mode in {"auto", "lmnt"}:
        lmnt_voice = str(os.getenv("WHATSAPP_LMNT_VOICE", "leah") or "leah").strip() or "leah"
        lmnt_bytes = lmnt_synthesize(cleaned, voice=lmnt_voice, lang=normalized_lang)
        lmnt_b64 = _wa_audio_bytes_to_ogg_b64(lmnt_bytes or b"", input_suffix=".mp3")
        if lmnt_b64:
            return {"audio_b64": lmnt_b64, "engine": "lmnt"}

    # piper = fallback local handled in WhatsAppHandler._send_voice_message
    return None


def _wa_tokenize_text(text: str) -> list[str]:
    cleaned = _clean_caption_text(text or "")
    if not cleaned:
        return []
    return [
        token.casefold()
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", cleaned)
        if token
    ]


def _wa_pronunciation_metrics(expected_phrase: str, transcript: str) -> dict[str, Any]:
    expected_tokens = _wa_tokenize_text(expected_phrase)
    spoken_tokens = _wa_tokenize_text(transcript)
    expected_joined = " ".join(expected_tokens)
    spoken_joined = " ".join(spoken_tokens)

    ratio = (
        difflib.SequenceMatcher(a=expected_joined, b=spoken_joined).ratio()
        if expected_joined and spoken_joined
        else 0.0
    )

    expected_unique = list(dict.fromkeys(expected_tokens))
    spoken_set = set(spoken_tokens)
    expected_set = set(expected_unique)
    coverage = (
        sum(1 for token in expected_unique if token in spoken_set) / len(expected_unique)
        if expected_unique
        else 0.0
    )

    score = int(round((ratio * 0.7 + coverage * 0.3) * 100))
    if spoken_tokens and len(spoken_tokens) < max(2, len(expected_tokens) // 3):
        score = min(score, 64)
    score = max(1, min(100, score))

    missing_words = [token for token in expected_unique if token not in spoken_set][:5]
    extra_words = [token for token in dict.fromkeys(spoken_tokens) if token not in expected_set][:5]

    return {
        "score": score,
        "similarity_ratio": round(ratio, 3),
        "coverage_ratio": round(coverage, 3),
        "missing_words": missing_words,
        "extra_words": extra_words,
    }


def _wa_feedback_fallback(
    expected_phrase: str,
    transcript: str,
    score: int,
    metrics: dict[str, Any],
    lesson_tip: str = "",
) -> str:
    if score >= 88:
        level = "Excelente"
    elif score >= 74:
        level = "Muito bom"
    elif score >= 60:
        level = "Bom progresso"
    else:
        level = "Vamos ajustar"

    spoken_preview = _clean_caption_text(transcript or "")
    if len(spoken_preview) > 160:
        spoken_preview = f"{spoken_preview[:157]}..."
    target_preview = _clean_caption_text(expected_phrase or "")
    if len(target_preview) > 160:
        target_preview = f"{target_preview[:157]}..."

    missing_words = metrics.get("missing_words") or []
    missing_msg = ", ".join(missing_words[:4]) if missing_words else ""
    tip_line = _clean_caption_text(lesson_tip or "")

    lines = [
        "🎙️ *Feedback de pronúncia*",
        f"📊 Resultado: *{score}/100* ({level})",
        f"🗣️ Você disse: _{spoken_preview or '...' }_",
        f"🎯 Frase-alvo: _{target_preview or '...' }_",
    ]
    if missing_msg:
        lines.append(f"🔎 Ajuste de palavras: *{missing_msg}*")
    if tip_line:
        lines.append(f"💡 Dica da lição: {tip_line}")
    lines.append(f"🔁 Repita: _{target_preview or expected_phrase}_")
    return "\n".join(lines)


def _wa_transcribe_audio_file(audio_path: Path, preferred_lang: str = "en") -> tuple[dict[str, Any] | None, list[str]]:
    language = (preferred_lang or "").strip().lower().split("-")[0]
    errors: list[str] = []
    attempts: list[tuple[str, Any]] = []

    if OPENAI_API_KEY:
        attempts.append(("openai_whisper", _openai_transcribe_audio_file))
    if DEEPGRAM_ENABLED and DEEPGRAM_API_KEY:
        attempts.append(("deepgram_stt", None))
    if LOCAL_WHISPER_ENABLED and WhisperModel is not None:
        attempts.append(("local_whisper", None))

    for source, fn in attempts:
        try:
            if source == "openai_whisper" and fn:
                payload = fn(audio_path, language or "en")
                text = _clean_caption_text(payload.get("text", ""))
                if not text:
                    parts = []
                    for seg in payload.get("segments", []) or []:
                        seg_text = _clean_caption_text(seg.get("text", ""))
                        if seg_text:
                            parts.append(seg_text)
                    text = " ".join(parts).strip()
                if text:
                    return {
                        "text": text,
                        "language": payload.get("language") or language,
                        "source": source,
                    }, errors
                errors.append(f"{source}: transcrição vazia")
                continue

            if source == "deepgram_stt":
                deepgram_payload = {
                    "model": DEEPGRAM_MODEL,
                    "smart_format": "true",
                    "punctuate": "true",
                    "detect_language": "true",
                }
                if language:
                    deepgram_payload["language"] = language
                with audio_path.open("rb") as audio_file:
                    resp = http_requests.post(
                        "https://api.deepgram.com/v1/listen",
                        headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
                        data=deepgram_payload,
                        files={"audio": (audio_path.name, audio_file, "application/octet-stream")},
                        timeout=300,
                    )
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code} {resp.text[:180]}")
                payload = resp.json()
                raw_segments, detected_lang = _deepgram_payload_to_raw_segments(payload)
                normalized = _normalize_transcript_segments(raw_segments)
                parts = []
                for seg in normalized:
                    seg_text = _clean_caption_text(seg.get("text", ""))
                    if seg_text:
                        parts.append(seg_text)
                if not parts:
                    alt = (
                        payload.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                    alt_clean = _clean_caption_text(alt)
                    if alt_clean:
                        parts = [alt_clean]
                text = " ".join(parts).strip()
                if text:
                    return {
                        "text": text,
                        "language": detected_lang or language,
                        "source": source,
                    }, errors
                errors.append(f"{source}: transcrição vazia")
                continue

            if source == "local_whisper":
                model = _get_local_whisper_model()
                seg_iter, info = model.transcribe(
                    str(audio_path),
                    language=language or None,
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
                parts = []
                for seg in seg_iter:
                    seg_text = _clean_caption_text(getattr(seg, "text", ""))
                    if seg_text:
                        parts.append(seg_text)
                text = " ".join(parts).strip()
                if text:
                    return {
                        "text": text,
                        "language": getattr(info, "language", "") or language,
                        "source": source,
                    }, errors
                errors.append(f"{source}: transcrição vazia")
                continue
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    return None, errors


def _wa_build_learner_context(message_data: dict | None, *, lang: str = "en") -> LearnerContext:
    key = {}
    if isinstance(message_data, dict):
        raw_key = message_data.get("key")
        if isinstance(raw_key, dict):
            key = raw_key

    candidates = [
        key.get("remoteJid"),
        key.get("participant"),
        (message_data or {}).get("sender"),
        (message_data or {}).get("senderPnJid"),
        (message_data or {}).get("chatId"),
    ]
    phone = ""
    for value in candidates:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if len(digits) >= 8:
            phone = digits
            break

    return LearnerContext(
        learner_key=_normalize_learner_key(phone or "whatsapp-default", default="whatsapp-default"),
        channel="whatsapp",
        display_name="",
        target_lang=_normalize_lang(lang, default="en"),
        level="A1",
        native_lang="pt",
        source_system="whatsapp",
        external_phone=phone,
    )


def _wa_ai_pronunciation_feedback(
    *,
    audio_url: str = "",
    expected_phrase: str = "",
    lang: str = "en",
    lesson: dict[str, Any] | None = None,
    message_data: dict[str, Any] | None = None,
    audio_message: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected_clean = _clean_caption_text(expected_phrase or "")
    lesson_tip = _clean_caption_text((lesson or {}).get("tip", "")) if isinstance(lesson, dict) else ""
    learner = _wa_build_learner_context(message_data, lang=lang)
    mime_hint = _clean_caption_text((audio_message or {}).get("mimetype", ""))
    media_payload = {}
    audio_bytes = b""
    encoded_audio = ""
    detected_mime = ""

    try:
        if _WA_CLIENT and isinstance(message_data, dict):
            media_payload = _WA_CLIENT.get_media_base64_from_message(message_data)
        encoded_audio, detected_mime = _wa_extract_media_base64(media_payload)
    except Exception as exc:
        media_payload = {"error": str(exc)}

    if not encoded_audio and audio_url:
        download_url = str(audio_url).strip()
        if download_url and not download_url.startswith("http") and _WA_CLIENT:
            download_url = f"{_WA_CLIENT.base_url.rstrip('/')}/{download_url.lstrip('/')}"
        if download_url.startswith("http"):
            headers = {}
            if _WA_CLIENT:
                token = _WA_CLIENT.instance_token()
                headers["apikey"] = token or _WA_CLIENT.api_key
            try:
                resp = http_requests.get(download_url, headers=headers or None, timeout=30)
                if resp.status_code == 200 and resp.content:
                    if "application/json" in str(resp.headers.get("Content-Type", "")).lower():
                        payload = resp.json()
                        encoded_audio, detected_mime = _wa_extract_media_base64(payload)
                    else:
                        audio_bytes = resp.content
                        detected_mime = str(resp.headers.get("Content-Type", ""))
            except Exception:
                pass

    if encoded_audio and not audio_bytes:
        compact = re.sub(r"\s+", "", encoded_audio)
        compact += "=" * ((4 - len(compact) % 4) % 4)
        try:
            audio_bytes = base64.b64decode(compact, validate=False)
        except Exception as exc:
            return {
                "feedback": (
                    "⚠️ Recebi seu áudio, mas não consegui decodificar para análise agora.\n\n"
                    f"🎯 Frase da lição: _{expected_clean or 'sem frase definida'}_\n"
                    "Envie outro áudio em seguida para tentarmos de novo."
                ),
                "error": f"decode_failed: {exc}",
            }

    if not audio_bytes:
        return {
            "feedback": (
                "⚠️ Não consegui acessar o áudio enviado para análise detalhada.\n\n"
                f"🎯 Frase da lição: _{expected_clean or 'sem frase definida'}_\n"
                f"💡 Dica: {lesson_tip or 'fale em blocos curtos e com ritmo constante.'}\n"
                "Tente reenviar o áudio para eu corrigir melhor."
            ),
            "error": "audio_not_found",
            "media_debug": media_payload if isinstance(media_payload, dict) else {},
        }

    suffix = _wa_guess_audio_suffix(detected_mime or mime_hint)
    with tempfile.TemporaryDirectory(prefix="wa_audio_") as tmp:
        audio_path = Path(tmp) / f"whatsapp_input{suffix}"
        audio_path.write_bytes(audio_bytes)
        transcription, stt_errors = _wa_transcribe_audio_file(audio_path, preferred_lang=lang or "en")

    transcript = _clean_caption_text((transcription or {}).get("text", ""))
    if not transcript:
        return {
            "feedback": (
                "🎤 Recebi seu áudio, mas ainda não consegui entender bem o que foi dito.\n\n"
                "Fale um pouco mais perto do microfone e repita a frase completa.\n"
                f"🎯 Frase-alvo: _{expected_clean or 'sem frase definida'}_"
            ),
            "error": "stt_empty",
            "stt_attempts": stt_errors,
        }

    metrics = _wa_pronunciation_metrics(expected_clean or transcript, transcript)
    score = int(metrics.get("score", 0) or 0)
    fallback_feedback = _wa_feedback_fallback(
        expected_clean or transcript,
        transcript,
        score,
        metrics,
        lesson_tip=lesson_tip,
    )
    feedback_text = fallback_feedback
    provider = None

    if has_text_ai_provider():
        system = (
            "Você é um professor de pronúncia para brasileiros aprendendo inglês por WhatsApp. "
            "Seja direto, humano e motivador."
        )
        prompt = (
            "Dados da tentativa:\n"
            f"- Frase-alvo: {expected_clean or transcript}\n"
            f"- Transcrição do aluno: {transcript}\n"
            f"- Score estimado: {score}/100\n"
            f"- Similaridade: {metrics.get('similarity_ratio', 0)}\n"
            f"- Cobertura da frase: {metrics.get('coverage_ratio', 0)}\n"
            f"- Palavras ausentes: {', '.join(metrics.get('missing_words', [])) or 'nenhuma'}\n"
            f"- Dica da lição: {lesson_tip or 'sem dica adicional'}\n\n"
            "Retorne APENAS JSON no formato:\n"
            '{"feedback":"..."}\n\n'
            "Regras para feedback:\n"
            "- Escreva em PT-BR.\n"
            "- 4 a 7 linhas curtas para WhatsApp.\n"
            "- Inclua score em uma linha (ex: 78/100).\n"
            "- Inclua no fim uma linha 'Repita:' com até 8 palavras em inglês.\n"
            "- Use *negrito* e _itálico_ de forma leve.\n"
            "- Não use markdown de lista."
        )
        try:
            ai_raw, provider = chat_with_fallback(
                system,
                prompt,
                max_tokens=260,
                temperature=0.35,
            )
            parsed = _extract_json_payload_from_text(ai_raw or "") if ai_raw else None
            ai_feedback = _clean_caption_text((parsed or {}).get("feedback", "")) if isinstance(parsed, dict) else ""
            if ai_feedback:
                feedback_text = ai_feedback
        except Exception:
            provider = provider or None

    _ADAPTIVE_STORE.record_pronunciation_attempt(
        learner,
        expected_phrase=expected_clean or transcript,
        transcript=transcript,
        score=score,
        metadata={
            "stt_source": (transcription or {}).get("source", ""),
            "lesson_tip": lesson_tip,
            "similarity_ratio": metrics.get("similarity_ratio"),
            "coverage_ratio": metrics.get("coverage_ratio"),
            "missing_words": metrics.get("missing_words", []),
            "extra_words": metrics.get("extra_words", []),
        },
    )

    return {
        "feedback": feedback_text,
        "score": score,
        "transcript": transcript,
        "expected_phrase": expected_clean,
        "stt_source": (transcription or {}).get("source", ""),
        "stt_attempts": stt_errors,
        "provider": provider,
        "metrics": metrics,
    }


def _wa_ai_chat_reply(
    *,
    user_text: str = "",
    student: dict[str, Any] | None = None,
    lang: str = "en",
) -> dict[str, Any]:
    text = _clean_caption_text(user_text or "")
    if not text:
        return {}

    level = _clean_caption_text((student or {}).get("level", "A1"))
    lesson_phrase = ""
    if _WA_CURRICULUM and isinstance(student, dict):
        try:
            idx = int(student.get("lesson_index", 0) or 0)
            lesson = _WA_CURRICULUM.get(lang or "en", idx)
            if lesson:
                lesson_phrase = _clean_caption_text(getattr(lesson, "phrase", ""))
        except Exception:
            lesson_phrase = ""

    fallback_reply = (
        "Great effort! Keep your answer in English and use 1-2 short sentences.\n"
        "Try this model: _Today I practiced for 10 minutes._\n"
        "Now tell me: what did you study today?"
    )

    if not has_text_ai_provider():
        return {"reply": fallback_reply, "voice_text": fallback_reply}

    system = (
        "You are an English coach on WhatsApp for Brazilian learners. "
        "Your reply must be warm, concise, and practical."
    )
    prompt = (
        f"Student level: {level}\n"
        f"Current lesson phrase: {lesson_phrase or 'n/a'}\n"
        f"Student message: {text}\n\n"
        "Return ONLY JSON:\n"
        '{"reply":"...", "voice_text":"..."}\n\n'
        "Rules:\n"
        "- Write in PT-BR with short English practice chunks.\n"
        "- reply: 3 to 6 short lines suitable for WhatsApp.\n"
        "- Include one simple corrected English model sentence if useful.\n"
        "- End with one question to keep conversation going.\n"
        "- voice_text: max 220 chars, natural spoken version, no markdown.\n"
        "- Do not mention AI.\n"
    )

    try:
        raw, _provider = chat_with_fallback(
            system,
            prompt,
            max_tokens=260,
            temperature=0.6,
        )
    except Exception:
        raw = None

    parsed = _extract_json_payload_from_text(raw or "") if raw else None
    if not isinstance(parsed, dict):
        return {"reply": fallback_reply, "voice_text": fallback_reply}

    reply = _clean_caption_text(parsed.get("reply", ""))
    voice_text = _clean_caption_text(parsed.get("voice_text", ""))
    if not reply:
        reply = fallback_reply
    if not voice_text:
        voice_text = reply
    return {"reply": reply, "voice_text": voice_text}


def _get_wa_handler():
    """Inicializa os componentes WhatsApp de forma lazy (thread-safe)."""
    global _WA_CLIENT, _WA_STUDENTS, _WA_CURRICULUM, _WA_SCHEDULER, _WA_HANDLER
    if _WA_HANDLER:
        return _WA_HANDLER
    with _WA_LOCK:
        if _WA_HANDLER:
            return _WA_HANDLER
        try:
            from whatsapp import (
                EvolutionClient, StudentManager,
                LessonCurriculum, LessonScheduler, WhatsAppHandler,
            )
            _WA_CLIENT = EvolutionClient()
            _WA_STUDENTS = StudentManager()
            _WA_CURRICULUM = LessonCurriculum()
            _WA_SCHEDULER = LessonScheduler(
                client=_WA_CLIENT,
                students=_WA_STUDENTS,
                curriculum=_WA_CURRICULUM,
                models_dir=BASE_DIR / "models",
            )
            _WA_SCHEDULER.start()
            _WA_HANDLER = WhatsAppHandler(
                client=_WA_CLIENT,
                students=_WA_STUDENTS,
                curriculum=_WA_CURRICULUM,
                scheduler=_WA_SCHEDULER,
                ai_feedback_fn=_wa_ai_pronunciation_feedback,
                ai_chat_fn=_wa_ai_chat_reply,
                ai_tts_fn=_wa_ai_tts_audio_b64,
            )
            print("   WhatsApp:   ✅ Mini-aulas ativas")
        except Exception as exc:
            print(f"   WhatsApp:   ❌ Falha ao inicializar: {exc}")
            return None
    return _WA_HANDLER


def _wa_manager_url() -> str:
    """Retorna URL do Evolution Manager acessível pelo navegador do usuário."""
    external = str(os.getenv("EVOLUTION_SERVER_URL", "")).strip().rstrip("/")
    if external:
        return f"{external}/manager/"

    if _WA_CLIENT and getattr(_WA_CLIENT, "base_url", ""):
        base = str(_WA_CLIENT.base_url).rstrip("/")
        if "evolution-api" in base:
            base = base.replace("evolution-api", "localhost")
        return f"{base}/manager/"

    return "http://localhost:8080/manager/"


@app.route("/whatsapp/webhook", methods=["GET", "POST"])
@app.route("/whatsapp/webhook/<path:event_suffix>", methods=["POST"])
def whatsapp_webhook(event_suffix: str | None = None):
    """Webhook da Evolution API — recebe eventos de mensagens."""
    # GET é usado pela Evolution API para verificar o endpoint
    if request.method == "GET":
        return jsonify({"status": "ok", "service": "shadowing-whatsapp"}), 200

    if not WHATSAPP_ENABLED:
        return jsonify({"error": "WhatsApp not enabled"}), 503

    handler = _get_wa_handler()
    if not handler:
        return jsonify({"error": "WhatsApp handler not available"}), 503

    try:
        event = request.get_json(force=True, silent=True) or {}
        if event_suffix:
            normalized = str(event_suffix or "").strip().replace("/", "_")
            event.setdefault("event", normalized)
        result = handler.handle_event(event)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/whatsapp/status", methods=["GET"])
def whatsapp_status():
    """Status do serviço WhatsApp e estatísticas de alunos."""
    if not WHATSAPP_ENABLED:
        return jsonify({"enabled": False}), 200

    handler = _get_wa_handler()
    students_count = {}
    if _WA_STUDENTS:
        students_count = _WA_STUDENTS.count()

    from whatsapp.evolution_client import EvolutionClient as _EC
    instance_status = {}
    if _WA_CLIENT:
        instance_status = _WA_CLIENT.instance_status()

    return jsonify({
        "enabled": True,
        "instance": os.getenv("EVOLUTION_INSTANCE", "shadowing"),
        "evolution_api_url": os.getenv("EVOLUTION_API_URL", "http://localhost:8080"),
        "students": students_count,
        "instance_status": instance_status,
        "scheduler_running": _WA_SCHEDULER._running if _WA_SCHEDULER else False,
    })


@app.route("/whatsapp/qrcode", methods=["GET"])
def whatsapp_qrcode():
    """Retorna o QR Code para conectar o WhatsApp ao Evolution API."""
    if not WHATSAPP_ENABLED:
        return jsonify({"error": "WhatsApp not enabled"}), 503
    handler = _get_wa_handler()
    if not _WA_CLIENT:
        return jsonify({"error": "Client not initialized"}), 503
    number = str(request.args.get("number", "")).strip()
    result = _WA_CLIENT.get_qrcode(number=number or None)
    payload = result if isinstance(result, dict) else {"data": result}
    payload.setdefault("manager_url", _wa_manager_url())
    if payload.get("count") == 0 and not payload.get("code") and not payload.get("qrcode"):
        payload.setdefault(
            "hint",
            "Sem QR ativo agora. Gere novamente em alguns segundos ou abra o manager da Evolution.",
        )
    return jsonify(payload)


@app.route("/whatsapp/setup", methods=["POST"])
def whatsapp_setup():
    """Cria a instância no Evolution API e configura o webhook."""
    if not WHATSAPP_ENABLED:
        return jsonify({"error": "WhatsApp not enabled"}), 503
    handler = _get_wa_handler()
    if not _WA_CLIENT:
        return jsonify({"error": "Client not initialized"}), 503

    data = request.get_json(force=True, silent=True) or {}
    webhook_url = data.get("webhook_url", "")
    if not webhook_url:
        # Auto-detect:
        # - Docker internal network (Evolution chama shadowing-practice:5000)
        # - Fallback para host público da requisição
        host = str(request.host or "").split(":")[0].strip().lower()
        evo_url = str(os.getenv("EVOLUTION_API_URL", "")).strip().lower()
        if host in {"127.0.0.1", "localhost"} and "evolution-api" in evo_url:
            webhook_url = "http://shadowing-practice:5000/whatsapp/webhook"
        else:
            webhook_url = f"{request.host_url.rstrip('/')}/whatsapp/webhook"

    try:
        existing_names = {
            str(item.get("name", "")).strip()
            for item in _WA_CLIENT.fetch_instances()
            if isinstance(item, dict)
        }
    except Exception:
        existing_names = set()

    if _WA_CLIENT.instance in existing_names:
        instance_result = {
            "ok": True,
            "message": "Instance already exists",
            "instanceName": _WA_CLIENT.instance,
        }
    else:
        instance_result = _WA_CLIENT.create_instance(webhook_url=webhook_url)
    webhook_result = _WA_CLIENT.set_webhook(webhook_url)
    return jsonify({
        "instance": instance_result,
        "webhook": webhook_result,
        "webhook_url": webhook_url,
        "manager_url": _wa_manager_url(),
    })


@app.route("/whatsapp/send", methods=["POST"])
def whatsapp_send():
    """Envia uma lição manualmente para um aluno (uso admin/teste)."""
    if not WHATSAPP_ENABLED:
        return jsonify({"error": "WhatsApp not enabled"}), 503

    data = request.get_json(force=True, silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    if not phone:
        return jsonify({"error": "Field 'phone' is required"}), 400

    handler = _get_wa_handler()
    if not handler:
        return jsonify({"error": "WhatsApp handler not available"}), 503

    if not _WA_STUDENTS or not _WA_STUDENTS.exists(phone):
        if not _WA_STUDENTS:
            return jsonify({"error": "Students manager not available"}), 503
        _WA_STUDENTS.register(
            phone,
            lang=data.get("lang", "en"),
            level=data.get("level", "A1"),
        )

    result = _WA_SCHEDULER.send_now(phone)
    return jsonify(result)


@app.route("/whatsapp/students", methods=["GET"])
def whatsapp_students():
    """Lista todos os alunos cadastrados."""
    if not WHATSAPP_ENABLED:
        return jsonify({"error": "WhatsApp not enabled"}), 503
    if not _WA_STUDENTS:
        _get_wa_handler()
    if not _WA_STUDENTS:
        return jsonify({"error": "Students manager not available"}), 503
    return jsonify({
        "count": _WA_STUDENTS.count(),
        "students": _WA_STUDENTS.all_students(),
    })


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Limpeza automática na inicialização
    _cleanup_old_audio()
    stats = _get_audio_stats()
    ollama_model = _resolve_ollama_model(force_refresh=True)

    print("\n🎧 Shadowing Practice for Fluency")
    print(f"   LMNT:       {'✅ Configurado' if LMNT_API_KEY else '❌ Sem chave'}")
    print(
        "   Piper local: "
        f"{'✅ Ativo' if piper_available() else '❌ Modelo ausente/inativo'}"
    )
    print(f"   Piper idiomas: {', '.join(piper_supported_languages()) or 'nenhum'}")
    print(f"   OpenRouter: {'✅ Configurado' if OPENROUTER_API_KEY else '❌ Sem chave'}")
    print(f"   OpenAI Chat: {'✅ Configurado' if OPENAI_API_KEY else '❌ Sem chave'}")
    print(
        "   Ollama IA: "
        f"{'✅ Ativo (' + ollama_model + ')' if ollama_model else '❌ Indisponível'}"
    )
    print(
        "   Deepgram STT/TTS: "
        f"{'✅ Configurado' if DEEPGRAM_API_KEY and DEEPGRAM_ENABLED else '❌ Sem chave/inativo'}"
    )
    print(
        "   YouTube transcript: "
        f"{'✅ Disponível' if YouTubeTranscriptApi else '❌ Dependência ausente'}"
    )
    print(
        "   yt-dlp fallback: "
        f"{'✅ Disponível' if yt_dlp else '❌ Dependência ausente'}"
    )
    print(
        "   Local Whisper fallback: "
        f"{'✅ Ativo' if WhisperModel and LOCAL_WHISPER_ENABLED else '❌ Inativo'}"
    )
    print(
        "   OpenAI audio fallback: "
        f"{'✅ Configurado' if OPENAI_API_KEY else '❌ Sem chave'}"
    )
    print(f"   Áudio cache: {stats['file_count']} arquivos ({stats['total_size_mb']} MB)")
    # WhatsApp mini-aulas
    if WHATSAPP_ENABLED:
        _get_wa_handler()
    else:
        print("   WhatsApp:   ⏸️  Desativado (WHATSAPP_ENABLED=0)")
    print("   Acesse: http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
