#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Este instalador WSL suporta distros baseadas em Debian/Ubuntu (apt-get)."
  exit 1
fi

APT_RUNNER=()
if ((EUID != 0)); then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo nao encontrado. Rode este instalador como root ou instale/configure sudo no WSL."
    exit 1
  fi
  APT_RUNNER=("sudo")
fi

PACKAGES=()

if ! command -v python3 >/dev/null 2>&1; then
  PACKAGES+=("python3")
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  PACKAGES+=("python3-venv")
fi

if ! command -v pip3 >/dev/null 2>&1; then
  PACKAGES+=("python3-pip")
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  PACKAGES+=("ffmpeg")
fi

if ((${#PACKAGES[@]} > 0)); then
  echo "Instalando dependencias do sistema no WSL: ${PACKAGES[*]}"
  "${APT_RUNNER[@]}" apt-get update
  "${APT_RUNNER[@]}" apt-get install -y "${PACKAGES[@]}"
fi

if [[ ! -f ".env" && -f ".env.example" ]]; then
  cp ".env.example" ".env"
  echo "Arquivo .env criado a partir de .env.example"
fi

if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
fi

PYTHON_BIN=".venv/bin/python"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt

cat <<'EOF'

Instalacao WSL concluida.

Para iniciar a aplicacao no WSL:
  bash ./run.sh

Se preferir iniciar do Windows:
  powershell -ExecutionPolicy Bypass -File .\run_windows_wsl.ps1
EOF
