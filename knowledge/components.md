# Orion - Component Reference

## VoiceAssistant (voice_assistant.py)

**Role**: Main orchestrator. Owns all components, manages lifecycle and conversation flow.

**Key methods**:
- `__init__()` — Initialize all components
- `start()` — Setup face, greet user, start listeners
- `_start_listeners()` — Start clap detector + wake word detector
- `_on_activate()` — Thread-safe activation handler
- `_conversation_loop()` — Record → interpret → execute → speak loop
- `_process_commands()` — Execute command list sequentially

**Threading**: Uses `threading.Lock` to prevent concurrent activations. Daemon threads for background tasks.

---

## ClapDetector (clap_detector.py)

**Role**: Detect double-clap pattern for activation.

**Algorithm**: RMS energy spike detection with timing constraints.

| Parameter | Value | Description |
|-----------|-------|-------------|
| SAMPLE_RATE | 44100 Hz | Audio stream rate |
| ENERGY_THRESHOLD | 0.25 | RMS threshold for clap detection |
| MIN_GAP_SEC | 0.15 | Minimum time between two claps |
| MAX_GAP_SEC | 1.5 | Maximum time between two claps |
| COOLDOWN_SEC | 2.0 | Cooldown between activations |

**Calibration**: Run `python calibrate.py` to measure ambient noise and tune threshold.

---

## WakeWordDetector (wake_word_detector.py)

**Role**: Detect "Orion" wake word using continuous VAD + Whisper.

**Algorithm**:
1. Continuous 16kHz audio stream with callback
2. Silero VAD state machine: SILENT → SPEECH → SILENCE_AFTER_SPEECH
3. Pre-buffer captures 320ms before speech onset
4. On speech end: clean audio → Whisper transcribe → regex match

**Wake word regex**: `\b[oó]r[iye](?:ão|[oa][nm]?)\b`
- Matches: orion, órion, orian, orião, oriom, oreon, oryon, oriam
- Word boundary prevents false positives (e.g., "laboratório")

| Parameter | Value |
|-----------|-------|
| SAMPLE_RATE | 16000 Hz |
| VAD_THRESHOLD | 0.35 |
| MIN_SPEECH_SEC | 0.12 |
| SILENCE_AFTER_SEC | 0.35 |
| BUFFER_SECONDS | 3.0 |
| PRE_BUFFER_BLOCKS | 10 (320ms) |
| COOLDOWN | 3.0s |

**Wake word prefix**: Extracts text after "Orion" (e.g., "Orion, abre Chrome" → "abre Chrome" passed as prefix).

---

## SpeechRecognizer (speech_recognizer.py)

**Role**: Record user speech and transcribe to text.

**Pipeline**:
1. Open 16kHz mono stream (512-sample blocks)
2. Skip first 0.5s (grace period for TTS bleed)
3. VAD-based recording: accumulate while speech detected
4. Stop on 1.5s silence OR 15s max duration
5. Audio cleaning: bandpass filter (100-3400 Hz) + spectral noise reduction
6. Whisper transcription (large-v3, CUDA, pt, beam_size=3)
7. Filter segments by no_speech_prob < 0.6
8. Fix known transcription errors (e.g., "oração" → "horas são")

| Parameter | Value |
|-----------|-------|
| SAMPLE_RATE | 16000 Hz |
| VAD_THRESHOLD | 0.4 |
| SILENCE_TIMEOUT | 1.5s |
| MAX_DURATION | 15.0s |
| INITIAL_SILENCE_TIMEOUT | 8.0s |

---

## CommandInterpreter (command_interpreter.py)

**Role**: Convert transcribed text to structured commands via LLM.

**Pipeline**:
1. Load conversation history (last 10 turns from memory.json)
2. Build system prompt: JARVIS personality + command mappings + learnings
3. Send to Ollama `/api/chat` with JSON schema format
4. Parse and validate JSON response
5. Save compact version to history

**LLM Settings**:
| Setting | Value |
|---------|-------|
| URL | http://localhost:11434 |
| Model | qwen2.5:1.5b |
| Temperature | 0.1 |
| num_ctx | 4096 |
| num_predict | 300 |
| Format | JSON schema |

**Response format**:
```json
{
  "commands": [
    {
      "action": "open_app",
      "target": "chrome",
      "args": "",
      "reply": "Chrome entrando online, Senhor."
    }
  ]
}
```

**Validation**: Ensures actions exist, solo actions don't mix, no repeated duplicates.

**Background tasks** (every 10 interactions):
- History cleanup: LLM evaluates and removes bad pairs
- Learning extraction: insights saved to learnings.json (max 30)

**Data files**:
- `~/.local/share/orion/memory.json` — conversation history
- `~/.local/share/orion/learnings.json` — extracted patterns

---

## CommandExecutor (command_executor.py)

**Role**: Execute system commands and return response text.

**Dispatch**: `_do_{action}(target, args)` methods. See `knowledge/commands-reference.md`.

**Special behaviors**:
- `_do_weather()` — fetches wttr.in, summarizes with LLM
- `_do_analyze_screen()` — screenshot → moondream vision → LLM summary (VRAM swap)
- `_do_analyze_selection()` — clipboard text → LLM analysis (translate/summarize/correct)
- `_do_news()` — DuckDuckGo scrape → LLM summary
- `_do_shutdown()` — requires confirmation before executing

---

## TTS (tts.py)

**Role**: Text-to-speech with multiple backends and interrupt detection.

**Backend priority**:
1. **XTTS v2** (GPU) — voice cloning from `assets/voice_ref.wav`, 24kHz
2. **Kokoro** (CPU) — phoneme-based, pitch shift 0.88, speed 1.35x
3. **Piper** — binary pipe to aplay
4. **espeak-ng** — command-line fallback

**Interrupt monitoring**: During playback, monitors mic RMS. If > 0.15 for 3 consecutive chunks → stop playback.

**VRAM management**:
- `free_vram()` — move XTTS model to CPU (for vision model)
- `reclaim_vram()` — move XTTS back to GPU

---

## VAD (vad.py)

**Role**: Silero Voice Activity Detection wrapper.

Loads model via `torch.hub.load('snakers4/silero-vad')`. Provides speech probability per audio chunk.

---

## audio_utils (audio_utils.py)

**Role**: Audio preprocessing.

**Functions**:
- `bandpass_filter(audio, sr, low=100, high=3400)` — scipy butterworth filter
- `reduce_noise(audio, sr, noise_profile)` — noisereduce spectral gating
- `clean_audio(audio, sr, noise_profile)` — applies both in sequence

---

## FaceAnimator (face.py)

**Role**: Terminal ASCII face with state-based animations.

**States**: IDLE (breathing), LISTENING (scanning), SPEAKING (wave), PROCESSING

Runs in daemon thread, clears/redraws 5-line face + scrolling log output below.

---

## commands.py

**Role**: Command registry, app mappings, smart home config, response templates.

**Key data structures**:
- `COMMANDS` — dict of all available actions with descriptions
- `APP_MAP` — 20+ app name → executable mappings
- `MONITORS` — multi-monitor coordinates (ultrawide, notebook, inferior)
- `SMART_HOME_DEVICES` — IFTTT device event mappings
- `RESPONSE_TEMPLATES` — categorized random response phrases
