# Orion - Setup & Running

## Prerequisites

- Ubuntu (tested on 22.04+)
- NVIDIA GPU with CUDA support (recommended for STT/TTS performance)
- Python 3.10+
- Microphone + speakers

## Installation

```bash
# Full automated install (6 stages)
chmod +x install.sh
./install.sh
```

### Install Stages

1. **System packages** — apt-get install (portaudio, espeak-ng, ffmpeg, wmctrl, xdotool, etc.)
2. **Python venv** — creates `.venv`, installs PyTorch with CUDA 12.4, then requirements.txt
3. **Ollama** — installs Ollama, pulls qwen2.5:1.5b + moondream models
4. **Piper TTS** — downloads binary for architecture (x86_64/aarch64), installs to ~/.local/bin
5. **Voice model** — downloads pt_BR-faber-medium from HuggingFace to ~/.local/share/piper
6. **XTTS v2** — downloads model files to ~/.local/share/tts (optional GPU TTS)

### Post-Install

- Place a voice reference WAV at `assets/voice_ref.wav` for XTTS voice cloning
- Run `python calibrate.py` to calibrate clap detection threshold for your environment

## Running

```bash
# Start (foreground)
./start.sh

# Start (background, logs to ~/.local/share/orion/orion.log)
./start.sh &

# Stop
./stop.sh
```

### What start.sh does

1. Checks if `ollama serve` is running, starts it if not
2. Activates Python virtual environment (`.venv`)
3. Sets `LD_LIBRARY_PATH` for CUDA libraries (faster-whisper needs this)
4. Runs `python main.py`

### Startup sequence timing

| Step | Approximate Time |
|------|-----------------|
| Load Whisper large-v3 (first time) | ~1-2 min |
| Load Whisper (cached) | ~10-20s |
| Load Silero VAD | instant |
| Noise calibration | 1s |
| Ollama warmup | 2-5s |
| Load XTTS v2 | ~10-30s |
| **Total first run** | **~2-3 min** |
| **Total cached** | **~30-60s** |

## Usage

### Activation Methods

1. **Double clap** — two claps within 0.15-1.5s gap
2. **Wake word** — say "Orion" (or variations: órion, orian, orião)

### Conversation Flow

1. Orion activates → speaks listening phrase
2. User speaks command in Portuguese
3. Orion interprets → executes → speaks response
4. User can continue speaking more commands
5. Say "para", "pare", "chega", or "dispensado" to end

### Example Commands (Portuguese)

| Say | What Happens |
|-----|-------------|
| "Abre o Chrome" | Opens Google Chrome |
| "Fecha tudo" | Closes all windows |
| "Que horas são?" | Speaks current time |
| "Como está o tempo?" | Fetches and speaks weather |
| "Aumenta o volume" | Volume +10% |
| "Tira um print" | Takes screenshot |
| "Desligar" | Shutdown (asks confirmation) |
| "Analisa a tela" | Screenshots and describes screen content |

### Interrupting Orion

Speak while Orion is talking — if your voice exceeds 0.15 RMS for 3 consecutive chunks, TTS stops.

## Troubleshooting

### Clap detection too sensitive/insensitive
Run `python calibrate.py` and adjust `ENERGY_THRESHOLD` in `clap_detector.py`.

### Wake word not detecting
- Check microphone: `arecord -d 3 test.wav && aplay test.wav`
- Ambient noise may be too high — VAD threshold may need lowering
- Try speaking "Orion" more clearly/loudly

### Ollama not responding
```bash
# Check if running
curl http://localhost:11434/api/tags
# Restart
ollama serve &
```

### CUDA/GPU issues
- Verify: `python -c "import torch; print(torch.cuda.is_available())"`
- Check LD_LIBRARY_PATH includes CUDA libs from venv
- start.sh handles this, but manual run needs the export

### TTS not working
Falls back automatically: XTTS → Kokoro → Piper → espeak-ng. If none work:
```bash
# Test espeak
espeak-ng -v pt-br "teste"
# Test Piper
echo "teste" | ~/.local/bin/piper --model ~/.local/share/piper/pt_BR-faber-medium.onnx --output-raw | aplay -r 22050 -f S16_LE
```
