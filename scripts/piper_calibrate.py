#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import (
    CONFIG_DIR,
    PIPER_MODEL_PATHS,
    PIPER_PROFILE_LABELS,
    STUDY_TARGET_LANGS,
    piper_synthesize_to_file,
)


DEFAULT_PROFILES = ["balanced", "chat", "lesson", "story", "question", "expressive"]
DEFAULT_PHRASES_PATH = CONFIG_DIR / "piper_calibration_phrases.json"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip()).strip("-")
    return normalized.lower() or "sample"


def _load_phrase_sets(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_model_path(lang: str, model_path_arg: str = "") -> Path:
    if model_path_arg.strip():
        path = Path(model_path_arg).expanduser()
    else:
        path = PIPER_MODEL_PATHS.get(lang, PIPER_MODEL_PATHS["en"])
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera uma bateria de amostras para calibracao do Piper.",
    )
    parser.add_argument("--lang", default="pt", help="Idioma base das frases (default: pt)")
    parser.add_argument(
        "--project-langs",
        action="store_true",
        help="Gera amostras para todos os idiomas principais do projeto",
    )
    parser.add_argument("--model", default="", help="Caminho opcional para o modelo .onnx")
    parser.add_argument(
        "--profiles",
        default=",".join(DEFAULT_PROFILES),
        help="Lista separada por virgula de perfis Piper",
    )
    parser.add_argument(
        "--phrases-file",
        default=str(DEFAULT_PHRASES_PATH),
        help="JSON com conjuntos de frases de calibracao",
    )
    parser.add_argument(
        "--phrase-id",
        action="append",
        default=[],
        help="Filtra por um ou mais ids de frase",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limita a quantidade de frases do conjunto",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Diretorio de saida. Default: /tmp/piper-calibration-<timestamp>",
    )
    parser.add_argument(
        "--skip-missing-models",
        action="store_true",
        help="Pula idiomas sem modelo Piper local configurado",
    )
    return parser


def _run_for_language(
    *,
    lang: str,
    model_arg: str,
    profiles: list[str],
    phrases_file: Path,
    phrase_ids: list[str],
    limit: int,
    output_dir: Path,
    skip_missing_models: bool,
) -> tuple[list[dict], list[dict]]:
    phrase_sets = _load_phrase_sets(phrases_file)
    selected = phrase_sets.get(lang)
    if not isinstance(selected, list) or not selected:
        raise SystemExit(f"Nenhum conjunto de frases encontrado para '{lang}' em {phrases_file}")

    if phrase_ids:
        allowed = {item.strip() for item in phrase_ids if item.strip()}
        selected = [item for item in selected if str(item.get("id", "")).strip() in allowed]
        if not selected:
            raise SystemExit(f"Nenhuma frase bateu com os ids informados para '{lang}'.")

    if limit and limit > 0:
        selected = selected[:limit]

    try:
        model_path = _resolve_model_path(lang, model_arg)
    except FileNotFoundError as exc:
        if skip_missing_models:
            return [], [{"lang": lang, "reason": str(exc)}]
        raise

    lang_dir = output_dir / lang
    lang_dir.mkdir(parents=True, exist_ok=True)

    print(f"Modelo [{lang}]: {model_path}")
    print(f"Saida  [{lang}]: {lang_dir}")

    samples = []
    for phrase in selected:
        text = str(phrase.get("text") or "").strip()
        if not text:
            continue
        phrase_id = str(phrase.get("id") or _slug(text[:32]))
        context_hint = str(phrase.get("context_hint") or "").strip()
        for profile in profiles:
            output_name = f"{phrase_id}__{profile}.wav"
            output_path = lang_dir / output_name
            result = piper_synthesize_to_file(
                text,
                output_path,
                lang=lang,
                request_options={
                    "profile": profile,
                    "context_hint": context_hint,
                    "model_path": str(model_path),
                },
            )
            if not result.get("ok"):
                raise SystemExit(
                    f"Falha ao gerar '{output_name}' ({lang}): {result.get('error') or 'erro desconhecido'}"
                )
            sample = {
                "lang": lang,
                "phrase_id": phrase_id,
                "profile": profile,
                "profile_label": PIPER_PROFILE_LABELS.get(profile, profile),
                "context_hint": context_hint,
                "text": text,
                "output_path": str(output_path),
                "meta": {
                    "settings": result.get("settings", {}),
                    "transformations": result.get("transformations", []),
                    "lexicon_matches": result.get("lexicon_matches", []),
                    "prepared_text": result.get("prepared_text", ""),
                    "voice_tuning": result.get("voice_tuning", {}),
                    "model_id": result.get("model_id", ""),
                },
            }
            samples.append(sample)
            print(f"[ok] {lang}/{output_name}")
    return samples, []


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    profiles = [
        item.strip().lower()
        for item in str(args.profiles or "").split(",")
        if item.strip()
    ]
    if not profiles:
        profiles = list(DEFAULT_PROFILES)

    phrases_file = Path(args.phrases_file).expanduser()
    languages = (
        sorted(STUDY_TARGET_LANGS)
        if args.project_langs
        else [str(args.lang or "pt").strip().lower()]
    )
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = (
        Path(args.output_dir).expanduser()
        if str(args.output_dir or "").strip()
        else Path("/tmp") / f"piper-calibration-project-{timestamp}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "languages": languages,
        "phrases_file": str(phrases_file),
        "profiles": profiles,
        "samples": [],
        "skipped": [],
    }
    print(f"Saida: {output_dir}")

    for lang in languages:
        samples, skipped = _run_for_language(
            lang=lang,
            model_arg=args.model,
            profiles=profiles,
            phrases_file=phrases_file,
            phrase_ids=args.phrase_id,
            limit=args.limit,
            output_dir=output_dir,
            skip_missing_models=args.skip_missing_models,
        )
        manifest["samples"].extend(samples)
        manifest["skipped"].extend(skipped)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Manifesto: {manifest_path}")
    print(f"Total de amostras: {len(manifest['samples'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
