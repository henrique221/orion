#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }

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
echo "  Setup do Orion - Assistente de Voz Local"
echo ""

# ── Pacotes do sistema ──────────────────────────────────────────────
info "Instalando dependencias do sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    portaudio19-dev \
    libsndfile1 \
    espeak-ng \
    alsa-utils \
    pulseaudio-utils \
    ffmpeg \
    wmctrl \
    curl \
    wget

# ── Python venv ─────────────────────────────────────────────────────
info "Criando ambiente virtual Python..."
python3 -m venv .venv
source .venv/bin/activate

info "Instalando dependencias Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── Ollama ──────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    info "Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    info "Ollama ja instalado."
fi

info "Iniciando Ollama..."
if ! pgrep -x ollama &>/dev/null; then
    ollama serve &>/dev/null &
    sleep 3
fi

info "Baixando modelo llama3.2 (pode demorar na primeira vez)..."
ollama pull llama3.2

# ── Piper TTS ───────────────────────────────────────────────────────
mkdir -p "$PIPER_BIN_DIR" "$PIPER_DIR"

if [ ! -f "$PIPER_BIN_DIR/piper" ]; then
    info "Instalando Piper TTS..."

    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  PIPER_ARCH="amd64" ;;
        aarch64) PIPER_ARCH="arm64" ;;
        *)
            warn "Arquitetura '$ARCH' nao suportada pelo Piper. Usando espeak-ng."
            PIPER_ARCH=""
            ;;
    esac

    if [ -n "$PIPER_ARCH" ]; then
        PIPER_TAR="piper_linux_${PIPER_ARCH}.tar.gz"
        PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/${PIPER_TAR}"

        info "Baixando Piper de $PIPER_URL ..."
        wget -q "$PIPER_URL" -O "/tmp/${PIPER_TAR}"
        tar -xzf "/tmp/${PIPER_TAR}" -C /tmp/
        cp /tmp/piper/piper "$PIPER_BIN_DIR/piper"
        chmod +x "$PIPER_BIN_DIR/piper"

        # Copiar libs do piper junto
        if [ -d /tmp/piper/lib ]; then
            cp -r /tmp/piper/lib "$PIPER_BIN_DIR/"
        fi
        # espeak-ng data que o piper precisa
        if [ -d /tmp/piper/espeak-ng-data ]; then
            cp -r /tmp/piper/espeak-ng-data "$PIPER_BIN_DIR/"
        fi

        rm -rf /tmp/piper "/tmp/${PIPER_TAR}"
        info "Piper instalado em $PIPER_BIN_DIR/piper"
    fi
else
    info "Piper ja instalado."
fi

# ── Modelo de voz pt-BR ────────────────────────────────────────────
if [ ! -f "$PIPER_DIR/${PIPER_VOICE}.onnx" ]; then
    info "Baixando modelo de voz pt-BR (faber-medium)..."

    VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR/faber/medium"
    wget -q "${VOICE_BASE}/${PIPER_VOICE}.onnx" -O "$PIPER_DIR/${PIPER_VOICE}.onnx"
    wget -q "${VOICE_BASE}/${PIPER_VOICE}.onnx.json" -O "$PIPER_DIR/${PIPER_VOICE}.onnx.json"

    info "Modelo de voz instalado em $PIPER_DIR/"
else
    info "Modelo de voz pt-BR ja instalado."
fi

# ── Fim ─────────────────────────────────────────────────────────────
echo ""
info "Setup concluido!"
echo ""
echo "  Para usar:"
echo "    source .venv/bin/activate"
echo "    python main.py"
echo ""
echo "  Para calibrar o detector de palmas:"
echo "    python calibrate.py"
echo ""
