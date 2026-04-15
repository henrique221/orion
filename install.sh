#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[+]${NC} $*"; }

PIPER_VERSION="2023.11.14-2"
PIPER_VOICE="pt_BR-faber-medium"
PIPER_DIR="$HOME/.local/share/piper"
PIPER_BIN_DIR="$HOME/.local/bin"

echo ""
echo "  ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗"
echo " ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║"
echo " ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║"
echo " ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║"
echo " ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║"
echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝"
echo ""
echo "  Instalacao completa do Orion"
echo ""

# ── 1. Pacotes do sistema ───────────────────────────────────────────
info "Instalando pacotes do sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    portaudio19-dev \
    libsndfile1 \
    espeak-ng \
    alsa-utils \
    pulseaudio-utils \
    ffmpeg \
    wmctrl \
    xdotool \
    xclip \
    xsel \
    scrot \
    imagemagick \
    curl \
    wget

# ── 2. Python venv ──────────────────────────────────────────────────
info "Criando ambiente virtual Python..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124 -q
pip install -r requirements.txt -q

# ── 3. Ollama ───────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    info "Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    info "Ollama ja instalado."
fi

if ! pgrep -f "ollama serve" &>/dev/null; then
    info "Iniciando Ollama..."
    ollama serve &>/dev/null &
    sleep 3
fi

info "Baixando modelo qwen2.5:1.5b..."
ollama pull qwen2.5:1.5b

info "Baixando modelo moondream (visão)..."
ollama pull moondream

# ── 4. Piper TTS ────────────────────────────────────────────────────
mkdir -p "$PIPER_BIN_DIR" "$PIPER_DIR"

if [ ! -f "$PIPER_BIN_DIR/piper" ]; then
    info "Instalando Piper TTS..."
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  PIPER_ARCH="amd64" ;;
        aarch64) PIPER_ARCH="arm64" ;;
        *) echo "Arquitetura $ARCH nao suportada pelo Piper."; PIPER_ARCH="" ;;
    esac

    if [ -n "$PIPER_ARCH" ]; then
        PIPER_TAR="piper_linux_${PIPER_ARCH}.tar.gz"
        wget -q "https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/${PIPER_TAR}" -O "/tmp/${PIPER_TAR}"
        tar -xzf "/tmp/${PIPER_TAR}" -C /tmp/
        cp /tmp/piper/piper "$PIPER_BIN_DIR/piper"
        chmod +x "$PIPER_BIN_DIR/piper"
        [ -d /tmp/piper/lib ] && cp -r /tmp/piper/lib "$PIPER_BIN_DIR/"
        [ -d /tmp/piper/espeak-ng-data ] && cp -r /tmp/piper/espeak-ng-data "$PIPER_BIN_DIR/"
        rm -rf /tmp/piper "/tmp/${PIPER_TAR}"
    fi
else
    info "Piper ja instalado."
fi

# ── 5. Modelo de voz pt-BR ──────────────────────────────────────────
if [ ! -f "$PIPER_DIR/${PIPER_VOICE}.onnx" ]; then
    info "Baixando modelo de voz pt-BR..."
    VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium"
    wget -q "${VOICE_BASE}/${PIPER_VOICE}.onnx" -O "$PIPER_DIR/${PIPER_VOICE}.onnx"
    wget -q "${VOICE_BASE}/${PIPER_VOICE}.onnx.json" -O "$PIPER_DIR/${PIPER_VOICE}.onnx.json"
else
    info "Modelo de voz pt-BR ja instalado."
fi

# ── 6. XTTS v2 (download do modelo) ─────────────────────────────────
XTTS_DIR="$HOME/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
if [ ! -f "$XTTS_DIR/model.pth" ]; then
    info "Baixando modelo XTTS v2..."
    mkdir -p "$XTTS_DIR"
    XTTS_BASE="https://huggingface.co/coqui/XTTS-v2/resolve/main"
    for f in config.json vocab.json speakers_xtts.pth model.pth; do
        wget -q "$XTTS_BASE/$f" -O "$XTTS_DIR/$f"
    done
    echo "I agree to the terms of the CPML license." > "$XTTS_DIR/tos_agreed.txt"
else
    info "XTTS v2 ja instalado."
fi

# ── Verificacao final ────────────────────────────────────────────────
echo ""
info "Verificando instalacao..."
echo ""
OK=true
for pkg in portaudio19-dev libsndfile1 espeak-ng pulseaudio-utils ffmpeg wmctrl xdotool xclip xsel scrot imagemagick; do
    if dpkg -s "$pkg" &>/dev/null; then
        echo "  $pkg: OK"
    else
        echo "  $pkg: FALHOU"
        OK=false
    fi
done
command -v ollama &>/dev/null && echo "  ollama: OK" || { echo "  ollama: FALHOU"; OK=false; }
[ -f "$PIPER_BIN_DIR/piper" ] && echo "  piper: OK" || { echo "  piper: FALHOU"; OK=false; }
[ -f "$PIPER_DIR/${PIPER_VOICE}.onnx" ] && echo "  voz pt-BR: OK" || { echo "  voz pt-BR: FALHOU"; OK=false; }
[ -f "$XTTS_DIR/model.pth" ] && echo "  xtts v2: OK" || { echo "  xtts v2: FALHOU"; OK=false; }
source .venv/bin/activate
python -c "import sounddevice, soundfile, numpy, requests, faster_whisper, TTS, torch, flask" 2>/dev/null && echo "  python deps: OK" || { echo "  python deps: FALHOU"; OK=false; }

echo ""
if $OK; then
    info "Tudo pronto!"
    echo ""
    echo "  Para usar:"
    echo "    source .venv/bin/activate"
    echo "    python main.py"
    echo ""
else
    echo "  Alguns componentes falharam. Verifique acima."
fi
