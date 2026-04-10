---
name: orion-audio-pipeline
description: Use when working with speech recognition, text-to-speech, wake word detection, clap detection, VAD, audio preprocessing, or any audio I/O - covers the full audio pipeline from microphone to speakers
---

# Orion Audio Pipeline

## Pipeline Overview

```
Mic → ClapDetector (44.1kHz, RMS energy)
    → WakeWordDetector (16kHz, Silero VAD + Whisper)
    → SpeechRecognizer (16kHz, VAD + bandpass + noise reduce + Whisper)
    → TTS Output (XTTS 24kHz / Kokoro / Piper / espeak-ng)
    → Speaker (with interrupt monitoring)
```

## Key Components

### Wake Word Detection
- Silero VAD (threshold 0.35) detects speech segments
- Pre-buffer captures 320ms before speech onset
- Whisper transcribes, regex matches "Orion" variants
- Regex: `\b[oó]r[iye](?:ão|[oa][nm]?)\b`

### Speech Recognition
- VAD threshold 0.4 (stricter than wake word)
- Stops on 1.5s silence or 15s max
- Cleans audio: bandpass 100-3400 Hz + spectral noise reduction
- Whisper large-v3 on CUDA, int8_float16, language=pt
- Fixes known transcription errors post-processing

### TTS (fallback chain)
1. **XTTS v2** — GPU, voice cloning from `assets/voice_ref.wav`
2. **Kokoro** — CPU, phoneme-based, pitch 0.88, speed 1.35x
3. **Piper** — binary pipe to aplay
4. **espeak-ng** — last resort

### Audio Cleaning (audio_utils.py)
- `bandpass_filter()` — scipy butterworth, 100-3400 Hz
- `reduce_noise()` — noisereduce spectral gating
- `clean_audio()` — both combined

### Interrupt Detection
- During TTS playback, monitors mic RMS > 0.15
- 3 consecutive detections → stop playback

## Tuning Parameters

See `knowledge/configuration.md` for all thresholds and their tuning notes.

## VRAM Management

- `TTS.free_vram()` — moves XTTS to CPU (for vision model use)
- `TTS.reclaim_vram()` — moves XTTS back to GPU
- Used during `analyze_screen` which needs moondream on GPU

## Detailed Reference

- `knowledge/components.md` — per-component algorithms and parameters
- `knowledge/configuration.md` — all audio thresholds with tuning guidance
