#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif [[ -x "venv/bin/python" ]]; then
  PY="venv/bin/python"
else
  PY="python3"
fi

LANG="pt"
TEXT=""
OUT="saida.wav"
USE_STDIN=0

PROFILE="${PIPER_PROFILE:-auto}"
CONTEXT_HINT="${PIPER_CONTEXT_HINT:-}"
SPEAKER_ID="${PIPER_SPEAKER_ID:-${PIPER_SPEAKER:-}}"
LENGTH_SCALE="${PIPER_LENGTH_SCALE:-}"
NOISE_SCALE="${PIPER_NOISE_SCALE:-}"
NOISE_W_SCALE="${PIPER_NOISE_W_SCALE:-}"
SENTENCE_SILENCE="${PIPER_SENTENCE_SILENCE:-}"
VOLUME="${PIPER_VOLUME:-}"
NORMALIZE_AUDIO=1
MODEL_PATH="${PIPER_MODEL_PATH:-}"
CONFIG_PATH="${PIPER_CONFIG_PATH:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdin)
      USE_STDIN=1
      shift
      ;;
    --lang)
      LANG="${2:-pt}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:-auto}"
      shift 2
      ;;
    --context|--context-hint)
      CONTEXT_HINT="${2:-}"
      shift 2
      ;;
    --speaker|--speaker-id)
      SPEAKER_ID="${2:-}"
      shift 2
      ;;
    --length-scale)
      LENGTH_SCALE="${2:-}"
      shift 2
      ;;
    --noise-scale)
      NOISE_SCALE="${2:-}"
      shift 2
      ;;
    --noise-w-scale)
      NOISE_W_SCALE="${2:-}"
      shift 2
      ;;
    --sentence-silence)
      SENTENCE_SILENCE="${2:-}"
      shift 2
      ;;
    --volume)
      VOLUME="${2:-}"
      shift 2
      ;;
    --model)
      MODEL_PATH="${2:-}"
      shift 2
      ;;
    --config)
      CONFIG_PATH="${2:-}"
      shift 2
      ;;
    --no-normalize)
      NORMALIZE_AUDIO=0
      shift
      ;;
    *)
      break
      ;;
  esac
done

if [[ "${USE_STDIN}" -eq 1 ]]; then
  OUT="${1:-saida.wav}"
  TEXT="$(cat)"
else
  TEXT="${1:-}"
  OUT="${2:-saida.wav}"
fi

if [[ -z "${TEXT}" ]]; then
  echo "Uso: ./tts_piper.sh [--lang en|pt|fr|es|de] [--profile auto|balanced|chat|lesson|story|question|expressive] \"Seu texto\" [saida.wav]" >&2
  echo "Ou:   echo \"Seu texto\" | ./tts_piper.sh --lang en --profile chat --stdin [saida.wav]" >&2
  echo "Extras: --context <hint> --speaker-id N --length-scale N --noise-scale N --noise-w-scale N --sentence-silence N --volume N --no-normalize" >&2
  exit 1
fi

"${PY}" - "${TEXT}" "${OUT}" "${LANG}" "${PROFILE}" "${CONTEXT_HINT}" "${SPEAKER_ID}" "${LENGTH_SCALE}" "${NOISE_SCALE}" "${NOISE_W_SCALE}" "${SENTENCE_SILENCE}" "${VOLUME}" "${NORMALIZE_AUDIO}" "${MODEL_PATH}" "${CONFIG_PATH}" <<'PY'
from pathlib import Path
import json
import sys

from app import piper_synthesize_to_file


text = sys.argv[1]
out_path = Path(sys.argv[2])
lang = sys.argv[3]
profile = sys.argv[4]
context_hint = sys.argv[5]
speaker_id = sys.argv[6]
length_scale = sys.argv[7]
noise_scale = sys.argv[8]
noise_w_scale = sys.argv[9]
sentence_silence = sys.argv[10]
volume = sys.argv[11]
normalize_audio = sys.argv[12] == "1"
model_path = sys.argv[13]
config_path = sys.argv[14]

options = {
    "profile": profile or "auto",
    "context_hint": context_hint or "",
    "normalize_audio": normalize_audio,
}
if speaker_id.strip():
    options["speaker_id"] = speaker_id.strip()
if length_scale.strip():
    options["length_scale"] = length_scale.strip()
if noise_scale.strip():
    options["noise_scale"] = noise_scale.strip()
if noise_w_scale.strip():
    options["noise_w_scale"] = noise_w_scale.strip()
if sentence_silence.strip():
    options["sentence_silence"] = sentence_silence.strip()
if volume.strip():
    options["volume"] = volume.strip()
if model_path.strip():
    options["model_path"] = model_path.strip()
if config_path.strip():
    options["config_path"] = config_path.strip()

result = piper_synthesize_to_file(
    text,
    out_path,
    lang=lang,
    request_options=options,
)

if not result.get("ok"):
    error = result.get("error") or "Falha desconhecida do Piper."
    print(f"Erro ao gerar áudio: {error}", file=sys.stderr)
    sys.exit(1)

public_meta = {
    "profile": result.get("profile"),
    "context_hint": result.get("context_hint"),
    "settings": result.get("settings"),
    "transformations": result.get("transformations"),
    "lexicon_matches": result.get("lexicon_matches"),
    "speaker_id": result.get("speaker_id"),
    "prepared_text": result.get("prepared_text"),
    "model_path": result.get("model_path"),
}
print(f"Áudio gerado: {out_path}")
print(json.dumps(public_meta, ensure_ascii=False, indent=2))
PY
