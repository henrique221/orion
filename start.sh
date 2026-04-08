#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Start ollama if not running
if ! pgrep -f "ollama serve" &>/dev/null; then
    echo "Iniciando Ollama..."
    ollama serve &>/dev/null &
    sleep 2
fi

source .venv/bin/activate

# CUDA libs do pip (faster-whisper)
NVIDIA_LIBS="$SCRIPT_DIR/.venv/lib/python3.12/site-packages/nvidia"
export LD_LIBRARY_PATH="$NVIDIA_LIBS/cublas/lib:$NVIDIA_LIBS/cudnn/lib:$NVIDIA_LIBS/cuda_nvrtc/lib:${LD_LIBRARY_PATH:-}"

if [ -t 0 ]; then
    python main.py
else
    LOG_DIR="$HOME/.local/share/orion"
    mkdir -p "$LOG_DIR"
    python main.py >> "$LOG_DIR/orion.log" 2>&1
fi
