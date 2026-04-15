# Orion - Dependencies Reference

## Python Packages (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| faster-whisper | 1.1.1 | Speech-to-text (Whisper), CUDA-optimized |
| sounddevice | 0.5.1 | Audio I/O (microphone/speaker streams) |
| soundfile | 0.12.1 | Audio file read/write |
| numpy | 1.26.4 | Numerical operations, audio array handling |
| requests | 2.32.3 | HTTP client (Ollama API, weather, IFTTT) |
| noisereduce | 3.0.3 | Spectral noise reduction |
| coqui-tts | 0.27.5 | XTTS v2 TTS model |
| torch | >=2.6.0 | PyTorch (CUDA index: cu124) |
| torchaudio | >=2.6.0 | Audio utilities for PyTorch |
| flask | >=3.0.0 | Web settings panel (UI) |
| pyyaml | >=6.0 | Read/write config.yaml (config.py) |

**Note**: torch/torchaudio installed from CUDA 12.4 index: `https://download.pytorch.org/whl/cu124`

### Implicit Dependencies (imported but not in requirements.txt)

| Package | Installed Via | Used In |
|---------|-------------|---------|
| scipy | noisereduce dep | audio_utils.py (bandpass filter) |

## System Packages (apt)

| Package | Purpose | Used By |
|---------|---------|--------|
| portaudio19-dev | Audio I/O library | sounddevice |
| libsndfile1 | Sound file support | soundfile |
| espeak-ng | Fallback TTS + phoneme generation | tts.py |
| alsa-utils | Audio utilities (aplay) | tts.py (Piper) |
| pulseaudio-utils | PulseAudio tools (pactl) | command_executor.py (volume) |
| ffmpeg | Audio/video processing | various |
| wmctrl | Window manager control | command_executor.py |
| xdotool | X11 automation | command_executor.py |
| xclip | Clipboard manager | command_executor.py |
| xsel | Clipboard manager (backup) | command_executor.py |
| scrot | Screenshot tool | command_executor.py |
| imagemagick | Image conversion (convert) | command_executor.py |
| curl | Download utility | install.sh |
| wget | Download utility | install.sh |

## ML Models

### Ollama Models (localhost:11434)

| Model | Size | Purpose | Used In |
|-------|------|---------|---------|
| qwen2.5:1.5b | ~1GB | Command interpretation, chat, summaries | command_interpreter.py, command_executor.py |
| moondream | ~1.7GB | Vision/screen analysis | command_executor.py |

### Whisper (faster-whisper)

| Setting | Value |
|---------|-------|
| Model | large-v3 |
| Device | cuda |
| Compute type | int8_float16 |
| Language | pt (Portuguese) |

### Silero VAD

| Setting | Value |
|---------|-------|
| Source | torch.hub: snakers4/silero-vad |
| Model | silero_vad |
| Auto-downloaded | Yes (first run) |

### XTTS v2 (Coqui TTS)

| Setting | Value |
|---------|-------|
| Cache path | ~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2 |
| Voice reference | assets/voice_ref.wav |
| Sample rate | 24000 Hz |
| Device | CUDA (GPU) with CPU fallback |

### Piper TTS (Fallback)

| Setting | Value |
|---------|-------|
| Binary | ~/.local/bin/piper |
| Model (pt-BR) | ~/.local/share/piper/pt_BR-faber-medium.onnx |
| Model (en-US) | ~/.local/share/piper/en_US-lessac-medium.onnx (~60MB) |
| Source | HuggingFace (rhasspy/piper-voices) |

## External Services (Optional)

| Service | Purpose | Config Location |
|---------|---------|----------------|
| IFTTT Webhooks | Smart home control | commands.py (IFTTT_KEY, IFTTT_URL) |
| wttr.in | Weather data (JSON) | command_executor.py |
| lite.duckduckgo.com | Web search, news | command_executor.py |

## Dependency Management Rules

From CLAUDE.md: whenever adding, removing, or changing a dependency, you MUST also update `install.sh`:
- apt packages → `apt-get install` block
- Ollama models → `ollama pull` commands
- Python packages → `requirements.txt` AND pip install steps
- Update verification checklist at bottom of `install.sh`

## Installation Stages (install.sh)

| Stage | What |
|-------|------|
| 1 | System packages (apt-get) |
| 2 | Python venv + pip install torch (CUDA) + requirements.txt |
| 3 | Ollama install + model pulls (qwen2.5:1.5b, moondream) |
| 4 | Piper TTS binary (architecture-dependent: x86_64/aarch64) |
| 5 | Piper voice model (pt_BR-faber-medium from HuggingFace) |
| 5b | Piper voice model en-US (en_US-lessac-medium from HuggingFace, ~60MB) |
| 6 | XTTS v2 model files (config, vocab, speakers, model weights) |
