# Orion - Configuration Reference

All configuration is currently hard-coded in source files. No external config file.

## Audio Parameters

### Clap Detection (clap_detector.py)

| Parameter | Value | Tuning Notes |
|-----------|-------|-------------|
| SAMPLE_RATE | 44100 Hz | Standard audio rate |
| ENERGY_THRESHOLD | 0.25 | Use `python calibrate.py` to tune |
| MIN_GAP_SEC | 0.15 | Minimum between two claps |
| MAX_GAP_SEC | 1.5 | Maximum between two claps |
| COOLDOWN_SEC | 2.0 | Prevents rapid re-triggers |

### Wake Word Detection (wake_word_detector.py)

| Parameter | Value | Tuning Notes |
|-----------|-------|-------------|
| SAMPLE_RATE | 16000 Hz | Whisper requirement |
| VAD_THRESHOLD | 0.35 | Lower = more sensitive to speech |
| MIN_SPEECH_SEC | 0.12 | Filter very short sounds |
| SILENCE_AFTER_SEC | 0.35 | How long to wait after speech ends |
| BUFFER_SECONDS | 3.0 | Max audio to buffer |
| PRE_BUFFER_BLOCKS | 10 | 320ms captured before speech detected |

### Speech Recognition (speech_recognizer.py)

| Parameter | Value | Tuning Notes |
|-----------|-------|-------------|
| SAMPLE_RATE | 16000 Hz | Whisper requirement |
| VAD_THRESHOLD | 0.4 | Higher than wake word (more strict) |
| SILENCE_TIMEOUT | 1.5s | Silence before ending recording |
| MAX_DURATION | 15.0s | Absolute max recording time |
| INITIAL_SILENCE_TIMEOUT | 8.0s | Timeout if no speech at start |

### Audio Cleaning (audio_utils.py)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Bandpass low | 100 Hz | Filters low-frequency noise |
| Bandpass high | 3400 Hz | Isolates voice frequencies |
| Noise profile | 1s calibration | Captured at startup |

### TTS (tts.py)

| Parameter | Value | Notes |
|-----------|-------|-------|
| XTTS sample rate | 24000 Hz | Fixed by model |
| Kokoro sample rate | 24000 Hz | Fixed by model |
| Kokoro pitch | 0.88 | Shift factor |
| Kokoro speed | 1.35x | Playback speed |
| Interrupt threshold | 0.15 RMS | User voice detection during TTS |
| Interrupt consecutive | 3 chunks | Required consecutive detections |

## LLM Settings

### Command Interpretation (command_interpreter.py)

| Setting | Value |
|---------|-------|
| OLLAMA_URL | http://localhost:11434 |
| MODEL | qwen2.5:1.5b |
| Temperature | 0.1 |
| num_ctx | 4096 |
| num_predict | 300 |
| MAX_HISTORY | 10 turns |
| MEMORY_FILE | ~/.local/share/orion/memory.json |
| LEARNINGS_FILE | ~/.local/share/orion/learnings.json |
| MAX_LEARNINGS | 30 |

### Command Execution LLM (command_executor.py)

| Setting | Value |
|---------|-------|
| OLLAMA_URL | http://localhost:11434 |
| LLM_MODEL | qwen2.5:1.5b |
| VISION_MODEL | moondream |
| DEMO_DURATION | 30 seconds |

## Whisper STT

| Setting | Value |
|---------|-------|
| Model | large-v3 |
| Device | cuda |
| Compute type | int8_float16 |
| Language | pt |
| Beam size | 3 |
| VAD filter | True |
| Initial prompt | "Orion, que horas são? Abre o Chrome..." |

## Application Mappings (commands.py)

| Name | Executable |
|------|-----------|
| chrome | google-chrome |
| firefox | firefox |
| terminal | gnome-terminal |
| nautilus/files | nautilus |
| code/vscode | code |
| cursor | cursor |
| spotify | spotify |
| discord | discord |
| slack | slack |
| telegram | telegram-desktop |
| obs | obs |
| gimp | gimp |
| vlc | vlc |
| steam | steam |
| calculator | gnome-calculator |
| settings | gnome-control-center |
| monitor | gnome-system-monitor |
| text | gnome-text-editor |

## Monitor Layout (commands.py)

| Name | Position (x, y, w, h) | Display |
|------|----------------------|---------|
| ultrawide | (0, 0, 2560, 1080) | HDMI-1-0 |
| notebook | (2560, 0, 1920, 1080) | Built-in |
| inferior | (903, 1080, 1920, 1080) | Below |

## Smart Home (commands.py)

| Device | On Event | Off Event |
|--------|----------|-----------|
| varanda | varanda_on | varanda_off |
| piscina | piscina_on | piscina_off |

IFTTT webhook URL: `https://maker.ifttt.com/trigger/{event}/with/key/{IFTTT_KEY}`

## Weather (command_executor.py)

| Setting | Value |
|---------|-------|
| WEATHER_LOCATION | Conceição da Aparecida |
| Primary API | wttr.in (JSON format) |
| Fallback | DuckDuckGo search |

## Web Settings Panel

| Setting | Value |
|---------|-------|
| Host | 127.0.0.1 (localhost only) |
| Port | 5000 |
| Launch | `python run_web.py` |
| Debug mode | Enabled by default (disable with `--no-debug`) |

Editable content paths:
- Knowledge files: `knowledge/*.md`
- Claude skills: `.claude/skills/*/SKILL.md`

## Data Directories

| Path | Purpose |
|------|---------|
| ~/.local/share/orion/ | App data (memory, learnings, logs) |
| ~/.local/share/tts/ | XTTS v2 model cache |
| ~/.local/share/piper/ | Piper voice model |
| ~/.local/bin/piper | Piper binary |
